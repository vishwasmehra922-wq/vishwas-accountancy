from flask import Flask
import json

app = Flask(__name__)

chapters = [

{
"title": "1. साझेदारी लेखांकन",
"english": "Accounting for Partnership",
"theory": [
"साझेदारी दो या दो से अधिक व्यक्तियों के बीच किया गया समझौता है, जिसमें व्यवसाय के लाभ को आपस में बाँटने की सहमति होती है।",
"साझेदारी विलेख में लाभ-विभाजन अनुपात, पूँजी, वेतन, कमीशन, ब्याज आदि की शर्तें लिखी जाती हैं।",
"यदि Partnership Deed में कोई बात नहीं लिखी है तो Indian Partnership Act के प्रावधान लागू होते हैं।",
"Capital Account Fixed या Fluctuating हो सकता है।",
"Profit and Loss Appropriation Account के द्वारा साझेदारों में लाभ का वितरण किया जाता है।",
"Goodwill फर्म की प्रतिष्ठा और भविष्य में अधिक लाभ कमाने की क्षमता का मूल्य है।"
],
"formulas": [
"Interest on Capital = Capital × Rate × Time / 100",
"Interest on Drawings = Drawings × Rate × Time / 100",
"Average Profit = Total Profits / Number of Years",
"Super Profit = Average Profit − Normal Profit",
"Goodwill = Super Profit × Number of Years Purchase"
],
"questions": [
"साझेदारी की कोई चार विशेषताएँ लिखिए।",
"Partnership Deed क्या है?",
"Fixed और Fluctuating Capital में अंतर बताइए।",
"Goodwill क्या है?",
"Average Profit Method से Goodwill ज्ञात कीजिए।"
]
},

{
"title": "2. साझेदारी फर्म का पुनर्गठन",
"english": "Reconstitution of Partnership Firm",
"theory": [
"जब साझेदारों के बीच संबंध या लाभ-विभाजन अनुपात में परिवर्तन होता है तो साझेदारी फर्म का पुनर्गठन कहलाता है।",
"पुनर्गठन में सामान्यतः नया लाभ-विभाजन अनुपात और त्याग अनुपात निकाला जाता है।",
"Goodwill और Assets तथा Liabilities के पुनर्मूल्यांकन का समायोजन किया जाता है।",
"Revaluation Account का उपयोग assets और liabilities में हुए बदलाव का लाभ या हानि ज्ञात करने के लिए किया जाता है।"
],
"formulas": [
"Gaining Ratio = New Ratio − Old Ratio",
"Sacrificing Ratio = Old Ratio − New Ratio"
],
"questions": [
"साझेदारी फर्म का पुनर्गठन क्या है?",
"त्याग अनुपात क्या है?",
"लाभ अनुपात और त्याग अनुपात में अंतर बताइए।",
"Revaluation Account क्यों बनाया जाता है?",
"नए लाभ-विभाजन अनुपात की गणना कीजिए।"
]
},

{
"title": "3. नये साझेदार का प्रवेश",
"english": "Admission of a New Partner",
"theory": [
"जब कोई नया व्यक्ति साझेदारी फर्म में साझेदार के रूप में शामिल होता है तो इसे नए साझेदार का प्रवेश कहते हैं।",
"नया साझेदार फर्म में पूँजी और Goodwill ला सकता है।",
"नए साझेदार के प्रवेश पर पुराने साझेदारों का लाभ-विभाजन अनुपात बदल जाता है।",
"नए साझेदार द्वारा लाई गई Goodwill पुराने साझेदारों को उनके Sacrificing Ratio में दी जाती है।",
"Revaluation Account और Partners Capital Accounts में आवश्यक adjustments किए जाते हैं।"
],
"formulas": [
"New Ratio = Old Ratio − Sacrifice",
"New Partner's Share of Goodwill = Total Goodwill × New Partner's Share"
],
"questions": [
"नए साझेदार का प्रवेश क्या है?",
"नया साझेदार Goodwill क्यों लाता है?",
"Sacrificing Ratio क्या है?",
"Admission के समय Revaluation Account क्यों बनाया जाता है?",
"नए साझेदार के प्रवेश की Journal Entries लिखिए।"
]
},

{
"title": "4. साझेदार की निवृत्ति या मृत्यु",
"english": "Retirement or Death of a Partner",
"theory": [
"जब कोई साझेदार फर्म से अलग हो जाता है तो उसे साझेदार की निवृत्ति कहते हैं।",
"निवृत्त होने वाले साझेदार को उसका Capital, Goodwill और अन्य देय राशि दी जाती है।",
"निवृत्ति के बाद शेष साझेदारों का नया लाभ-विभाजन अनुपात निकाला जाता है।",
"साझेदार की मृत्यु होने पर उसके खाते में Capital, Goodwill, Profit आदि का समायोजन किया जाता है।"
],
"formulas": [
"Gaining Ratio = New Ratio − Old Ratio",
"Retiring Partner's Goodwill Share = Total Goodwill × Retiring Partner's Share"
],
"questions": [
"साझेदार की निवृत्ति क्या है?",
"निवृत्त साझेदार को कौन-कौन सी राशियाँ दी जाती हैं?",
"Gaining Ratio क्या है?",
"साझेदार की मृत्यु पर उसके खाते का निपटारा कैसे किया जाता है?",
"Retirement की Journal Entries कीजिए।"
]
},

{
"title": "5. साझेदारी फर्म का समापन",
"english": "Dissolution of Partnership Firm",
"theory": [
"जब साझेदारी फर्म का व्यवसाय पूरी तरह बंद कर दिया जाता है तो इसे फर्म का विघटन या Dissolution कहते हैं।",
"विघटन के समय Assets को बेचा जाता है और Liabilities का भुगतान किया जाता है।",
"Realisation Account बनाया जाता है।",
"Realisation Account से होने वाला लाभ या हानि साझेदारों में उनके Profit Sharing Ratio में बाँटा जाता है।",
"अंत में Partners Capital Accounts और Bank/Cash Account का निपटारा किया जाता है।"
],
"formulas": [
"Realisation Profit → Partners Capital Accounts",
"Realisation Loss → Partners Capital Accounts"
],
"questions": [
"Dissolution of Firm क्या है?",
"Realisation Account क्यों बनाया जाता है?",
"Realisation Profit कैसे बाँटा जाता है?",
"फर्म के विघटन की Journal Entries लिखिए।",
"Realisation Account तैयार कीजिए।"
]
},

{
"title": "6. कम्पनी लेखे — अंशों का निर्गमन",
"english": "Issue of Shares",
"theory": [
"Company अपनी पूँजी को छोटे-छोटे भागों में बाँटती है जिन्हें Shares कहा जाता है।",
"Shareholder कंपनी में अपने shares के अनुसार पूँजी लगाता है।",
"Shares को Par, Premium या कुछ परिस्थितियों में Discount पर जारी करने से संबंधित accounting entries की जाती हैं।",
"Share Capital को अलग-अलग stages जैसे Application, Allotment और Calls में प्राप्त किया जा सकता है।"
],
"formulas": [
"Amount Due = Number of Shares × Amount per Share",
"Application Money = Shares × Application Rate",
"Allotment Money = Shares × Allotment Rate"
],
"questions": [
"Share क्या है?",
"Share Capital क्या है?",
"Application और Allotment में अंतर बताइए।",
"Shares को Premium पर जारी करने की entries कीजिए।",
"Share Issue का numerical हल कीजिए।"
]
},

{
"title": "7. अंशों का हरण एवं पुनर्निर्गमन",
"english": "Forfeiture and Reissue of Shares",
"theory": [
"यदि shareholder shares पर देय राशि समय पर नहीं देता तो कंपनी उसके shares को Forfeit कर सकती है।",
"Forfeited Shares को कंपनी बाद में Reissue कर सकती है।",
"Forfeiture के समय Share Capital Account और संबंधित unpaid amount का adjustment किया जाता है।",
"Reissue के बाद बचा हुआ forfeiture amount Capital Reserve में transfer किया जा सकता है।"
],
"formulas": [
"Capital Reserve = Forfeited Amount − Reissue Discount"
],
"questions": [
"Forfeiture of Shares क्या है?",
"Shares को Forfeit क्यों किया जाता है?",
"Reissue of Shares क्या है?",
"Forfeiture की Journal Entry कीजिए।",
"Reissue और Capital Reserve का numerical हल कीजिए।"
]
},

{
"title": "8. ऋणपत्रों का निर्गमन",
"english": "Issue of Debentures",
"theory": [
"Debenture कंपनी द्वारा लिया गया दीर्घकालीन ऋण दर्शाता है।",
"Debenture holder कंपनी का creditor होता है।",
"Debentures को Par, Premium या Discount पर issue किया जा सकता है।",
"Debenture पर दिया जाने वाला Interest कंपनी के लिए expense होता है।"
],
"formulas": [
"Interest on Debentures = Face Value × Rate / 100",
"Annual Interest = Debenture Value × Interest Rate"
],
"questions": [
"Debenture क्या है?",
"Share और Debenture में अंतर बताइए।",
"Debentures को Premium पर issue करने की entry लिखिए।",
"Debenture Interest की गणना कीजिए।",
"Debenture Issue का numerical हल कीजिए।"
]
},

{
"title": "9. कम्पनी के वित्तीय विवरण",
"english": "Financial Statements of a Company",
"theory": [
"Financial Statements कंपनी की financial position और performance को दिखाते हैं।",
"Balance Sheet कंपनी की assets, liabilities और equity की स्थिति दिखाती है।",
"Statement of Profit and Loss से कंपनी का profit या loss पता चलता है।",
"Financial statements का उपयोग investors, management और अन्य users द्वारा किया जाता है।"
],
"formulas": [
"Profit = Revenue − Expenses",
"Assets = Equity + Liabilities"
],
"questions": [
"Financial Statements क्या हैं?",
"Balance Sheet क्या दिखाती है?",
"Statement of Profit and Loss का उद्देश्य क्या है?",
"Balance Sheet तैयार कीजिए।",
"Financial Statements के कोई चार उपयोग लिखिए।"
]
},

{
"title": "10. लेखांकन अनुपात",
"english": "Accounting Ratios",
"theory": [
"Accounting Ratios का उपयोग financial statements का analysis करने के लिए किया जाता है।",
"Ratios से कंपनी की liquidity, solvency और profitability के बारे में जानकारी मिलती है।",
"Current Ratio और Quick Ratio liquidity को मापने में उपयोगी हैं।",
"Debt Equity Ratio और Proprietary Ratio solvency से संबंधित हैं।",
"Gross Profit Ratio और Net Profit Ratio profitability से संबंधित हैं।"
],
"formulas": [
"Current Ratio = Current Assets / Current Liabilities",
"Quick Ratio = Quick Assets / Current Liabilities",
"Gross Profit Ratio = Gross Profit / Revenue × 100",
"Net Profit Ratio = Net Profit / Revenue × 100",
"Debt Equity Ratio = Debt / Equity"
],
"questions": [
"Accounting Ratio क्या है?",
"Current Ratio ज्ञात कीजिए।",
"Quick Ratio ज्ञात कीजिए।",
"Gross Profit Ratio ज्ञात कीजिए।",
"Debt Equity Ratio का अर्थ बताइए।"
]
},

{
"title": "11. रोकड़ प्रवाह विवरण",
"english": "Cash Flow Statement",
"theory": [
"Cash Flow Statement किसी अवधि में cash और cash equivalents में हुए बदलाव को दिखाता है।",
"Cash flows को Operating, Investing और Financing Activities में बाँटा जाता है।",
"Operating Activities व्यवसाय की मुख्य गतिविधियों से संबंधित होती हैं।",
"Investing Activities में assets और investments की खरीद-बिक्री शामिल होती है।",
"Financing Activities में capital और borrowings से संबंधित cash flows आते हैं।"
],
"formulas": [
"Net Cash Flow = Operating Cash Flow + Investing Cash Flow + Financing Cash Flow",
"Closing Cash = Opening Cash + Net Cash Flow"
],
"questions": [
"Cash Flow Statement क्या है?",
"Operating Activity क्या है?",
"Investing Activity क्या है?",
"Financing Activity क्या है?",
"Cash Flow Statement तैयार कीजिए।"
]
}

]

@app.route("/")
def home():

    data = json.dumps(chapters, ensure_ascii=False)

    return f"""
<!DOCTYPE html>
<html lang="hi">

<head><meta name="google-site-verification" content="4uDnZ3v253GGgoMmTkTM7a3v28clljd5dxfpUu1DA0k" />

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Class 12 Accountancy 📚</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #eef2f7;
    color: #222;
}}

header {{
    background: linear-gradient(135deg,#0f766e,#2563eb);
    color: white;
    text-align: center;
    padding: 35px 15px;
}}

header h1 {{
    font-size: 32px;
    margin: 5px;
}}

header p {{
    font-size: 16px;
}}

.container {{
    max-width: 900px;
    margin: auto;
    padding: 20px;
}}

.card {{
    background: white;
    margin: 15px 0;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0 4px 12px #0002;
    cursor: pointer;
}}

.card:active {{
    transform: scale(.98);
}}

.card h2 {{
    margin: 0 0 8px;
    color: #2563eb;
}}

.card p {{
    color: #666;
}}

.btn {{
    background: #2563eb;
    color: white;
    border: none;
    padding: 10px 16px;
    border-radius: 10px;
}}

#detail {{
    display: none;
    position: fixed;
    inset: 0;
    background: #0009;
    overflow-y: auto;
    padding: 15px;
}}

.box {{
    background: white;
    max-width: 800px;
    margin: 20px auto;
    padding: 22px;
    border-radius: 20px;
}}

.close {{
    float: right;
    background: #ef4444;
    color: white;
    border: none;
    padding: 9px 13px;
    border-radius: 8px;
}}

.theory {{
    background: #f8fafc;
    padding: 15px;
    border-radius: 12px;
    margin: 15px 0;
}}

.theory li {{
    margin: 10px 0;
    line-height: 1.6;
}}

.formula {{
    background: #eff6ff;
    padding: 15px;
    border-radius: 12px;
    margin: 15px 0;
}}

.question {{
    background: #fff7ed;
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
}}

</style>

</head>

<body>

<header>

<h1>📚 Class 12 Accountancy</h1>

<p>Theory • Formulas • Important Questions</p>

</header>

<div class="container">

<div id="chapters"></div>

</div>


<div id="detail">

<div class="box">

<button class="close" onclick="closeDetail()">✕ बंद करें</button>

<div id="content"></div>

</div>

</div>


<script>

var chapters = {data};

var list = document.getElementById("chapters");

chapters.forEach(function(chapter, index) {{

    list.innerHTML += `
    
    <div class="card" onclick="openChapter(${{index}})">
    
        <h2>${{chapter.title}}</h2>
        
        <p>${{chapter.english}}</p>
        
        <button class="btn">
        👆 पूरा Chapter देखें
        </button>
        
    </div>
    
    `;

}});


function openChapter(index) {{

    var c = chapters[index];

    var html = `

    <h1>${{c.title}}</h1>

    <h3>📖 Theory</h3>

    <div class="theory">

        <ul>
        
        ${{c.theory.map(function(t) {{
            return "<li>" + t + "</li>";
        }}).join("")}}
        
        </ul>

    </div>


    <h3>🧮 मुख्य Formula / Concepts</h3>

    <div class="formula">

        ${{c.formulas.map(function(f) {{
            return "<p>• " + f + "</p>";
        }}).join("")}}

    </div>


    <h3>📝 Important Questions</h3>

    ${{c.questions.map(function(q, i) {{
        return "<div class='question'><b>Q" + (i+1) + ".</b> " + q + "</div>";
    }}).join("")}}

    `;

    document.getElementById("content").innerHTML = html;

    document.getElementById("detail").style.display = "block";

}}


function closeDetail() {{

    document.getElementById("detail").style.display = "none";

}}

</script>

</body>

</html>
"""

