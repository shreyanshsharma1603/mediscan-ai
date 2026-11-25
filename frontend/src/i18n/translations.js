export const LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "es", label: "Spanish", native: "Español" },
  { code: "fr", label: "French", native: "Français" },
];

export const DOC_TYPE_LABELS = {
  blood_test: "Blood Test Report",
  urine_test: "Urine Test Report",
  prescription: "Prescription",
  radiology: "Radiology Report",
  discharge_summary: "Discharge Summary",
  clinical_notes: "Clinical Notes",
  other: "Other Medical Document",
};

const BASE_EN = {
  brand: "MediScan AI",
  tagline: "Understand Your Health. Decode Your Reports.",
  disclaimerShort:
    "Informational tool only — does not diagnose diseases, prescribe medications, or replace qualified healthcare professionals.",
  nav: {
    dashboard: "Dashboard",
    upload: "Upload Report",
    compare: "Compare Reports",
    timeline: "Health Timeline",
    prescriptions: "Prescription Reader",
    doctorSummary: "Doctor Summary",
    settings: "Settings & Language",
    logout: "Sign Out",
    login: "Sign In",
  },
  landing: {
    badge: "Multilingual Medical Document Intelligence",
    heroTitle: "Understand Your Health. Decode Your Reports.",
    heroSubtitle:
      "Upload blood tests, urine reports, prescriptions, radiology reports, or discharge summaries. Get source-grounded OCR extraction, printed reference-range analysis, longitudinal comparisons, and doctor-ready summaries in 8 languages.",
    ctaPrimary: "Start Analyzing Reports",
    ctaSecondary: "Sign In / Demo",
    featuresTitle: "Built for Clarity, Provenance & Clinical Safety",
  },
  auth: {
    signInTitle: "Welcome Back to MediScan AI",
    registerTitle: "Create Your Private Health Vault",
    email: "Email Address",
    password: "Password (min 6 chars)",
    fullName: "Full Name",
    language: "Preferred Language",
    consentLabel:
      "I understand MediScan AI is an informational literacy tool that does not diagnose conditions or replace a licensed clinician, and I consent to secure temporary document processing.",
    signInBtn: "Sign In",
    registerBtn: "Create Account",
    switchToRegister: "Need an account? Register",
    switchToLogin: "Already have an account? Sign In",
  },
  dashboard: {
    title: "Medical Intelligence Overview",
    subtitle: "Your private, source-grounded document archive and lab insights.",
    loadDemo: "Load Synthetic Demo Kit",
    uploadNew: "Scan New Document",
    totalDocs: "Uploaded Reports",
    abnormalFlags: "Out-of-Range Flags",
    verifyCount: "Need Verification",
    medsCount: "Extracted Medications",
    recentDocs: "Recent Medical Documents",
    emptyState: "No medical reports yet. Upload a PDF/image or load our synthetic demo kit to explore every module.",
  },
  upload: {
    title: "Smart Document Scanner",
    subtitle: "Upload PDF, JPG, JPEG, or PNG medical reports (max 15 MB) with instant preview and OCR.",
    dropzone: "Drag & drop your medical document here, or click to browse",
    formats: "Supported: PDF, JPG, JPEG, PNG • Max 15 MB • Private per-user storage",
    consentCheck: "I confirm this upload is for informational literacy and not emergency diagnosis.",
    analyzeBtn: "Extract & Analyze Document",
    uploading: "Extracting text & running AI analysis...",
  },
  analysis: {
    classification: "Document Classification",
    confidence: "Confidence",
    overrideLabel: "Correct Document Type",
    ocrQuality: "OCR Quality",
    plainSummary: "Plain-Language Summary",
    keyTakeaways: "Key Takeaways",
    viewDetailed: "Open Detailed Results",
    sourceVerify: "Source Text Verification",
    assistantTitle: "AI Medical Document Assistant",
    assistantSubtitle: "Ask questions grounded strictly in your uploaded report.",
    askPlaceholder: "Ask about a lab value, unit, medication, or finding...",
    askBtn: "Ask Assistant",
  },
  results: {
    title: "Detailed Structured Results",
    labTable: "Laboratory Values vs. Printed Reference Ranges",
    glossary: "Medical Terminology Glossary",
    questions: "Questions to Ask Your Doctor",
    uncertainties: "Verification & Uncertainty Notes",
    testName: "Test Name",
    result: "Result",
    refRange: "Printed Ref Range",
    status: "Status",
    source: "Source Provenance",
  },
  compare: {
    title: "Health Report Comparison",
    subtitle: "Match equivalent tests across two reports. Incompatible units are never falsely compared.",
    reportA: "Baseline Report (A)",
    reportB: "Follow-Up Report (B)",
    runCompare: "Compare Selected Reports",
    matchedTitle: "Comparable Tests Over Time",
    incompatibleTitle: "Excluded Due to Incompatible / Missing Units",
  },
  timeline: {
    title: "Medical Timeline & Comparable Trends",
    subtitle: "Chronological history and longitudinal biomarker charts (only where units match).",
    trendsTitle: "Comparable Biomarker Trends",
    docsTitle: "Chronological Document Feed",
  },
  prescriptions: {
    title: "Prescription Reader",
    subtitle: "Structured medication names, dosages, frequencies, and uncertainty flags printed on your documents.",
  },
  doctorSummary: {
    title: "Doctor Summary Generator",
    subtitle: "Generate a concise clinician-ready summary with uncertainties, questions, and PDF export.",
    selectDoc: "Select Medical Document",
    exportPdf: "Download Doctor Summary PDF",
  },
  settings: {
    title: "Settings, Language & Privacy Controls",
    subtitle: "Manage multilingual interface translation, automatic deletion retention, and data controls.",
    saveBtn: "Save Preferences",
    deleteAllBtn: "Delete Account & All Medical Data",
  },
  statuses: {
    within_range: "Within Range",
    below_range: "Below Range",
    above_range: "Above Range",
    reference_unavailable: "No Printed Range",
    manual_verification_needed: "Verify Value",
  },
};

const OVERRIDES = {
  hi: {
    tagline: "अपने स्वास्थ्य को समझें। अपनी रिपोर्ट को डिकोड करें।",
    disclaimerShort:
      "केवल जानकारी के लिए — यह रोगों का निदान नहीं करता, दवा नहीं लिखता और डॉक्टर का विकल्प नहीं है।",
    nav: {
      dashboard: "डैशबोर्ड",
      upload: "रिपोर्ट अपलोड करें",
      compare: "रिपोर्ट तुलना",
      timeline: "स्वास्थ्य टाइमलाइन",
      prescriptions: "प्रिस्क्रिप्शन रीडर",
      doctorSummary: "डॉक्टर सारांश",
      settings: "सेटिंग्स और भाषा",
      logout: "लॉग आउट",
      login: "लॉग इन",
    },
    dashboard: {
      title: "मेडिकल इंटेलिजेंस डैशबोर्ड",
      subtitle: "आपका निजी, स्रोत-आधारित मेडिकल दस्तावेज़ और लैब विश्लेषण।",
      loadDemo: "सिंथेटिक डेमो लोड करें",
      uploadNew: "नई रिपोर्ट स्कैन करें",
      totalDocs: "अपलोड की गई रिपोर्ट",
      abnormalFlags: "सीमा से बाहर मान",
      verifyCount: "सत्यापन आवश्यक",
      medsCount: "निकाली गई दवाएं",
      recentDocs: "हाल के मेडिकल दस्तावेज़",
      emptyState: "अभी कोई रिपोर्ट नहीं है। शुरू करने के लिए PDF/इमेज अपलोड करें या डेमो किट लोड करें।",
    },
    upload: {
      title: "स्मार्ट डॉक्यूमेंट स्कैनर",
      subtitle: "तुरंत प्रीव्यू और OCR के साथ PDF, JPG, JPEG या PNG अपलोड करें (अधिकतम 15 MB)।",
      dropzone: "अपनी मेडिकल रिपोर्ट यहाँ खींचें और छोड़ें, या फ़ाइल चुनें",
      analyzeBtn: "दस्तावेज़ निकालें और विश्लेषण करें",
      uploading: "टेक्स्ट निकाला जा रहा है और AI विश्लेषण चल रहा है...",
    },
    settings: {
      title: "सेटिंग्स, भाषा और गोपनीयता नियंत्रण",
      saveBtn: "प्राथमिकताएं सहेजें",
      deleteAllBtn: "खाता और सारा मेडिकल डेटा हटाएं",
    },
    statuses: {
      within_range: "सीमा के भीतर",
      below_range: "सीमा से कम",
      above_range: "सीमा से अधिक",
      reference_unavailable: "सीमा मुद्रित नहीं",
      manual_verification_needed: "सत्यापित करें",
    },
  },
  bn: {
    tagline: "আপনার স্বাস্থ্য বুঝুন। আপনার রিপোর্ট ডিকোড করুন।",
    disclaimerShort:
      "শুধুমাত্র তথ্যের জন্য — এটি রোগ নির্ণয় করে না, ওষুধ লিখে দেয় না এবং চিকিৎসকের বিকল্প নয়।",
    nav: {
      dashboard: "ড্যাশবোর্ড",
      upload: "রিপোর্ট আপলোড",
      compare: "রিপোর্ট তুলনা",
      timeline: "স্বাস্থ্য টাইমলাইন",
      prescriptions: "প্রেসক্রিপশন রিডার",
      doctorSummary: "ডাক্তার সারসংক্ষেপ",
      settings: "সেটিংস ও ভাষা",
      logout: "সাইন আউট",
      login: "সাইন ইন",
    },
    dashboard: {
      title: "মেডিকেল ইন্টেলিজেন্স ওভারভিউ",
      loadDemo: "সিন্থেটিক ডেমো লোড করুন",
      uploadNew: "নতুন রিপোর্ট স্ক্যান করুন",
      totalDocs: "আপলোড করা রিপোর্ট",
      abnormalFlags: "সীমার বাইরে মান",
      verifyCount: "যাচাই প্রয়োজন",
      medsCount: "ওষুধের তালিকা",
      recentDocs: "সাম্প্রতিক মেডিকেল নথি",
    },
    settings: {
      title: "সেটিংস, ভাষা ও গোপনীয়তা",
      saveBtn: "পছন্দ সংরক্ষণ করুন",
    },
    statuses: {
      within_range: "স্বাভাবিক সীমা",
      below_range: "সীমার নিচে",
      above_range: "সীমার উপরে",
      reference_unavailable: "সীমা মুদ্রিত নেই",
      manual_verification_needed: "যাচাই করুন",
    },
  },
  ta: {
    tagline: "உங்கள் உடல்நிலையைப் புரிந்து கொள்ளுங்கள். அறிக்கைகளை எளிதாக அறிக.",
    disclaimerShort:
      "தகவல் நோக்கத்திற்காக மட்டுமே — இது நோய்களைக் கண்டறியாது, மருந்து பரிந்துரைக்காது.",
    nav: {
      dashboard: "முகப்பு",
      upload: "அறிக்கை பதிவேற்று",
      compare: "அறிக்கை ஒப்பீடு",
      timeline: "உடல்நிலை காலவரிசை",
      prescriptions: "மருந்துச்சீட்டு வாசிப்பான்",
      doctorSummary: "மருத்துவர் சுருக்கம்",
      settings: "அமைப்புகள் & மொழி",
      logout: "வெளியேறு",
      login: "உள்நுழை",
    },
    dashboard: {
      title: "மருத்துவ நுண்ணறிவு முகப்பு",
      loadDemo: "மாதிரி அறிக்கைகளை ஏற்று",
      uploadNew: "புதிய ஆவணம் பதிவேற்று",
    },
    statuses: {
      within_range: "வரம்பிற்குள்",
      below_range: "வரம்பிற்குக் கீழ்",
      above_range: "வரம்பிற்கு மேல்",
      reference_unavailable: "வரம்பு இல்லை",
      manual_verification_needed: "சரிபார்க்கவும்",
    },
  },
  te: {
    tagline: "మీ ఆరోగ్యాన్ని అర్థం చేసుకోండి. మీ నివేదికలను సులభంగా చదవండి.",
    disclaimerShort:
      "సమాచార ప్రయోజనాల కోసం మాత్రమే — ఇది వ్యాధులను నిర్ధారించదు, మందులు సూచించదు.",
    nav: {
      dashboard: "డాష్‌బోర్డ్",
      upload: "నివేదిక అప్‌లోడ్",
      compare: "నివేదికల పోలిక",
      timeline: "ఆరోగ్య టైమ్‌లైన్",
      prescriptions: "ప్రిస్క్రిప్షన్ రీడర్",
      doctorSummary: "డాక్టర్ సారాంశం",
      settings: "సెట్టింగ్స్ & భాష",
      logout: "సైన్ అవుట్",
      login: "సైన్ ఇన్",
    },
    dashboard: {
      title: "మెడికల్ ఇంటెలిజెన్స్ డాష్‌బోర్డ్",
      loadDemo: "సింథటిక్ డెమో లోడ్ చేయండి",
      uploadNew: "కొత్త పత్రం స్కాన్ చేయండి",
    },
    statuses: {
      within_range: "పరిధిలో ఉంది",
      below_range: "పరిధి కంటే తక్కువ",
      above_range: "పరిధి కంటే ఎక్కువ",
      reference_unavailable: "పరిధి ముద్రించబడలేదు",
      manual_verification_needed: "ధృవీకరించండి",
    },
  },
  mr: {
    tagline: "तुमचे आरोग्य समजून घ्या. तुमचे अहवाल सोप्या भाषेत वाचा.",
    disclaimerShort:
      "केवळ माहितीसाठी — हे आजाराचे निदान करत नाही किंवा डॉक्टरांचा पर्याय नाही.",
    nav: {
      dashboard: "डॅशबोर्ड",
      upload: "अहवाल अपलोड",
      compare: "अहवाल तुलना",
      timeline: "आरोग्य टाइमलाइन",
      prescriptions: "प्रिस्क्रिप्शन रीडर",
      doctorSummary: "डॉक्टर सारांश",
      settings: "सेटिंग्ज आणि भाषा",
      logout: "साइन आउट",
      login: "साइन इन",
    },
    dashboard: {
      title: "मेडिकल इंटेलिजन्स डॅशबोर्ड",
      loadDemo: "सिंथेटिक डेमो लोड करा",
      uploadNew: "नवीन अहवाल स्कॅन करा",
    },
    statuses: {
      within_range: "मर्यादेत",
      below_range: "मर्यादेपेक्षा कमी",
      above_range: "मर्यादेपेक्षा जास्त",
      reference_unavailable: "मर्यादा छापलेली नाही",
      manual_verification_needed: "पडताळणी करा",
    },
  },
  es: {
    tagline: "Comprende tu salud. Descifra tus informes médicos.",
    disclaimerShort:
      "Solo informativo — no diagnostica enfermedades, no receta medicamentos ni reemplaza a un profesional médico.",
    nav: {
      dashboard: "Panel Principal",
      upload: "Subir Informe",
      compare: "Comparar Informes",
      timeline: "Línea Temporal",
      prescriptions: "Lector de Recetas",
      doctorSummary: "Resumen Médico",
      settings: "Ajustes e Idioma",
      logout: "Cerrar Sesión",
      login: "Iniciar Sesión",
    },
    dashboard: {
      title: "Panel de Inteligencia Médica",
      subtitle: "Tu archivo privado de documentos médicos y análisis de laboratorio.",
      loadDemo: "Cargar Kit Demo Sintético",
      uploadNew: "Escanear Documento",
      totalDocs: "Informes Subidos",
      abnormalFlags: "Fuera de Rango",
      verifyCount: "Requieren Revisión",
      medsCount: "Medicamentos Extraídos",
      recentDocs: "Documentos Médicos Recientes",
    },
    upload: {
      title: "Escáner Inteligente de Documentos",
      dropzone: "Arrastra y suelta tu informe médico aquí, o haz clic para elegir",
      analyzeBtn: "Extraer y Analizar Documento",
    },
    compare: {
      title: "Comparación de Informes",
      runCompare: "Comparar Informes",
    },
    settings: {
      title: "Ajustes, Idioma y Privacidad",
      saveBtn: "Guardar Preferencias",
    },
    statuses: {
      within_range: "En Rango",
      below_range: "Bajo Rango",
      above_range: "Sobre Rango",
      reference_unavailable: "Sin Rango Impreso",
      manual_verification_needed: "Verificar Valor",
    },
  },
  fr: {
    tagline: "Comprenez votre santé. Décodez vos comptes rendus.",
    disclaimerShort:
      "Outil informatif uniquement — ne pose aucun diagnostic, ne prescrit rien et ne remplace pas un médecin.",
    nav: {
      dashboard: "Tableau de bord",
      upload: "Importer un rapport",
      compare: "Comparer",
      timeline: "Chronologie Santé",
      prescriptions: "Ordonnances",
      doctorSummary: "Synthèse Médecin",
      settings: "Paramètres & Langue",
      logout: "Déconnexion",
      login: "Connexion",
    },
    dashboard: {
      title: "Vue d'ensemble Médicale",
      subtitle: "Votre coffre-fort privé de documents médicaux et d'analyses.",
      loadDemo: "Charger le kit démo synthétique",
      uploadNew: "Scanner un document",
      totalDocs: "Rapports importés",
      abnormalFlags: "Hors intervalle",
      verifyCount: "À vérifier",
      medsCount: "Médicaments extraits",
      recentDocs: "Documents médicaux récents",
    },
    upload: {
      title: "Scanner de Documents Intelligent",
      dropzone: "Glissez-déposez votre document médical ici, ou cliquez pour parcourir",
      analyzeBtn: "Extraire & Analyser",
    },
    compare: {
      title: "Comparaison de Rapports",
      runCompare: "Comparer les rapports",
    },
    settings: {
      title: "Paramètres, Langue & Confidentialité",
      saveBtn: "Enregistrer",
    },
    statuses: {
      within_range: "Dans la norme",
      below_range: "En dessous",
      above_range: "Au-dessus",
      reference_unavailable: "Norme absente",
      manual_verification_needed: "À vérifier",
    },
  },
};

function deepMerge(base, override) {
  if (!override) return base;
  const out = { ...base };
  for (const key of Object.keys(override)) {
    if (typeof override[key] === "object" && override[key] !== null && !Array.isArray(override[key])) {
      out[key] = deepMerge(base[key] || {}, override[key]);
    } else {
      out[key] = override[key];
    }
  }
  return out;
}

export function getTranslations(lang) {
  return deepMerge(BASE_EN, OVERRIDES[lang]);
}
