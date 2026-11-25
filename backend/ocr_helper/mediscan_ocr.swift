import Foundation
import PDFKit
import Vision
import AppKit
import ImageIO

struct LineResult: Codable {
    let text: String
    let confidence: Double
    let bbox: [Double]
}

struct PageResult: Codable {
    let page_number: Int
    let method: String
    let text: String
    let avg_confidence: Double
    let lines: [LineResult]
}

struct OCRResponse: Codable {
    let ok: Bool
    let page_count: Int
    let pages: [PageResult]
    let error: String?
}

func outputJSON(_ response: OCRResponse, exitCode: Int32 = 0) -> Never {
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.withoutEscapingSlashes]
    if let data = try? encoder.encode(response),
       let jsonStr = String(data: data, encoding: .utf8) {
        print(jsonStr)
    } else {
        print("{\"ok\":false,\"page_count\":0,\"pages\":[],\"error\":\"Failed to encode OCR JSON\"}")
    }
    exit(exitCode)
}

func normalizeCGImage(_ cgImage: CGImage) -> CGImage {
    let minDim = 640
    let w = max(cgImage.width, 1)
    let h = max(cgImage.height, 1)
    let scale = (w < minDim || h < minDim) ? max(Double(minDim) / Double(w), Double(minDim) / Double(h)) : 1.0
    let targetW = max(Int(Double(w) * scale), 1)
    let targetH = max(Int(Double(h) * scale), 1)

    guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
          let ctx = CGContext(
              data: nil,
              width: targetW,
              height: targetH,
              bitsPerComponent: 8,
              bytesPerRow: 0,
              space: colorSpace,
              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
          ) else {
        return cgImage
    }
    ctx.setFillColor(NSColor.white.cgColor)
    ctx.fill(CGRect(x: 0, y: 0, width: targetW, height: targetH))
    ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: targetW, height: targetH))
    return ctx.makeImage() ?? cgImage
}

func recognizeCGImage(_ cgImage: CGImage) throws -> (String, Double, [LineResult]) {
    let normalized = normalizeCGImage(cgImage)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["en-US"]

    let handler = VNImageRequestHandler(cgImage: normalized, options: [:])
    try handler.perform([request])

    guard let observations = request.results else {
        return ("", 0.0, [])
    }

    var lines: [LineResult] = []
    var textParts: [String] = []
    var confSum: Double = 0.0

    for obs in observations {
        guard let top = obs.topCandidates(1).first else { continue }
        let box = obs.boundingBox
        let conf = Double(top.confidence)
        lines.append(LineResult(
            text: top.string,
            confidence: conf,
            bbox: [Double(box.origin.x), Double(box.origin.y), Double(box.size.width), Double(box.size.height)]
        ))
        textParts.append(top.string)
        confSum += conf
    }

    let avgConf = lines.isEmpty ? 0.0 : confSum / Double(lines.count)
    return (textParts.joined(separator: "\n"), avgConf, lines)
}

func renderPDFPageToCGImage(_ page: PDFPage, scale: CGFloat = 2.5) -> CGImage? {
    let bounds = page.bounds(for: .mediaBox)
    let width = max(Int(bounds.width * scale), 1)
    let height = max(Int(bounds.height * scale), 1)

    guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
          let context = CGContext(
              data: nil,
              width: width,
              height: height,
              bitsPerComponent: 8,
              bytesPerRow: 0,
              space: colorSpace,
              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
          ) else {
        return nil
    }

    context.setFillColor(NSColor.white.cgColor)
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.saveGState()
    context.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: context)
    context.restoreGState()

    return context.makeImage()
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    outputJSON(OCRResponse(ok: false, page_count: 0, pages: [], error: "Missing file path argument"), exitCode: 1)
}

let filePath = args[1]
let fileURL = URL(fileURLWithPath: filePath)
let ext = fileURL.pathExtension.lowercased()

if ext == "pdf" {
    guard let pdfDoc = PDFDocument(url: fileURL) else {
        outputJSON(OCRResponse(ok: false, page_count: 0, pages: [], error: "Unable to open or parse PDF document"), exitCode: 2)
    }
    let pageCount = pdfDoc.pageCount
    if pageCount == 0 {
        outputJSON(OCRResponse(ok: false, page_count: 0, pages: [], error: "PDF contains zero pages"), exitCode: 2)
    }

    var pageResults: [PageResult] = []
    for idx in 0..<pageCount {
        guard let page = pdfDoc.page(at: idx) else { continue }
        let rawText = (page.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let nonWSCount = rawText.filter { !$0.isWhitespace }.count

        if nonWSCount >= 30 {
            let splitLines = rawText.components(separatedBy: .newlines).map {
                $0.trimmingCharacters(in: .whitespaces)
            }.filter { !$0.isEmpty }
            let lineObjs = splitLines.map { LineResult(text: $0, confidence: 0.99, bbox: []) }
            pageResults.append(PageResult(
                page_number: idx + 1,
                method: "pdf_text",
                text: rawText,
                avg_confidence: 0.99,
                lines: lineObjs
            ))
        } else {
            guard let cgImage = renderPDFPageToCGImage(page) else {
                pageResults.append(PageResult(
                    page_number: idx + 1,
                    method: "vision_ocr_failed",
                    text: rawText,
                    avg_confidence: 0.0,
                    lines: []
                ))
                continue
            }
            do {
                let (ocrText, avgConf, lines) = try recognizeCGImage(cgImage)
                pageResults.append(PageResult(
                    page_number: idx + 1,
                    method: "vision_ocr",
                    text: ocrText,
                    avg_confidence: avgConf,
                    lines: lines
                ))
            } catch {
                pageResults.append(PageResult(
                    page_number: idx + 1,
                    method: "vision_ocr_failed",
                    text: rawText,
                    avg_confidence: 0.0,
                    lines: []
                ))
            }
        }
    }
    outputJSON(OCRResponse(ok: true, page_count: pageCount, pages: pageResults, error: nil))
} else {
    guard let src = CGImageSourceCreateWithURL(fileURL as CFURL, nil),
          let cgImage = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        outputJSON(OCRResponse(ok: false, page_count: 0, pages: [], error: "Unable to decode image file"), exitCode: 2)
    }
    do {
        let (ocrText, avgConf, lines) = try recognizeCGImage(cgImage)
        let page = PageResult(
            page_number: 1,
            method: "vision_ocr",
            text: ocrText,
            avg_confidence: avgConf,
            lines: lines
        )
        outputJSON(OCRResponse(ok: true, page_count: 1, pages: [page], error: nil))
    } catch {
        outputJSON(OCRResponse(ok: false, page_count: 0, pages: [], error: "Vision OCR failed: \(error.localizedDescription)"), exitCode: 3)
    }
}
