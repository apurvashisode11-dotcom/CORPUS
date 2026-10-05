"""Texts the system writes into the live log, in English, Hindi and Marathi."""
T = {
 "en": {
  "t_results": "Check past ad results", "t_campaign": "Run Instagram ad campaign",
  "t_replies": "Prepare customer replies", "t_offers": "Send customer offers",
  "plan": "Plan ready: {n} tasks", "built": "{n} AI employees created",
  "ctr_reply": "{ctr}% click rate on the last campaign",
  "spend_req": "Need Rs {amount:,} for Instagram ads",
  "guard_escalate": "Rs {amount:,} is above {agent}'s Rs {limit:,} limit. Sent to owner.",
  "guard_block": "{agent} is not allowed to {action}. Blocked.",
  "approved": "Approved Rs {amount:,}", "rejected": "Rejected Rs {amount:,}",
  "tool_fail": "Did not respond.", "retry": "Retrying the task.",
  "reassign": "{tool} failed twice. Task handed over.",
  "tool_ad_platform": "Ad platform", "tool_email": "Email", "tool_memory": "Memory",
  "done": "Done: {title}", "escalate": "Could not finish: {title}. Asking the owner.",
  "complete": "All tasks finished", "partial": "Finished with problems. Please review."},
 "hi": {
  "t_results": "पिछले विज्ञापनों के नतीजे जाँचें", "t_campaign": "इंस्टाग्राम विज्ञापन अभियान चलाएँ",
  "t_replies": "ग्राहकों के जवाब तैयार करें", "t_offers": "ग्राहकों को ऑफ़र भेजें",
  "plan": "योजना तैयार: {n} काम", "built": "{n} AI कर्मचारी बनाए गए",
  "ctr_reply": "पिछले अभियान पर क्लिक दर {ctr}% रही",
  "spend_req": "इंस्टाग्राम विज्ञापनों के लिए Rs {amount:,} चाहिए",
  "guard_escalate": "Rs {amount:,} {agent} की Rs {limit:,} की सीमा से ज़्यादा है। मालिक को भेजा गया।",
  "guard_block": "{agent} को '{action}' करने की अनुमति नहीं है। रोका गया।",
  "approved": "Rs {amount:,} मंज़ूर किए", "rejected": "Rs {amount:,} अस्वीकार किए",
  "tool_fail": "जवाब नहीं दिया।", "retry": "दोबारा कोशिश की जा रही है।",
  "reassign": "{tool} दो बार विफल रहा। काम सौंप दिया गया।",
  "tool_ad_platform": "विज्ञापन प्लैटफ़ॉर्म", "tool_email": "ईमेल", "tool_memory": "मेमोरी",
  "done": "पूरा हुआ: {title}", "escalate": "पूरा नहीं हो सका: {title}। मालिक से पूछा जा रहा है।",
  "complete": "सभी काम पूरे हुए", "partial": "कुछ समस्याओं के साथ पूरा हुआ। कृपया देखें।"},
 "mr": {
  "t_results": "मागील जाहिरातींचे निकाल तपासा", "t_campaign": "इन्स्टाग्राम जाहिरात मोहीम राबवा",
  "t_replies": "ग्राहकांची उत्तरे तयार करा", "t_offers": "ग्राहकांना ऑफर पाठवा",
  "plan": "योजना तयार: {n} कामे", "built": "{n} AI कर्मचारी तयार केले",
  "ctr_reply": "मागील मोहिमेवर क्लिक दर {ctr}% होता",
  "spend_req": "इन्स्टाग्राम जाहिरातींसाठी Rs {amount:,} हवेत",
  "guard_escalate": "Rs {amount:,} ही {agent} च्या Rs {limit:,} मर्यादेपेक्षा जास्त आहे. मालकाकडे पाठवले.",
  "guard_block": "{agent} ला '{action}' करण्याची परवानगी नाही. थांबवले.",
  "approved": "Rs {amount:,} मंजूर केले", "rejected": "Rs {amount:,} नाकारले",
  "tool_fail": "प्रतिसाद दिला नाही.", "retry": "पुन्हा प्रयत्न केला जात आहे.",
  "reassign": "{tool} दोनदा अयशस्वी ठरले. काम सोपवले.",
  "tool_ad_platform": "जाहिरात प्लॅटफॉर्म", "tool_email": "ईमेल", "tool_memory": "मेमरी",
  "done": "पूर्ण झाले: {title}", "escalate": "पूर्ण होऊ शकले नाही: {title}. मालकाला विचारत आहे.",
  "complete": "सर्व कामे पूर्ण झाली", "partial": "काही अडचणींसह पूर्ण झाले. कृपया तपासा."},
}


def t(lang: str, key: str, **kw) -> str:
    table = T.get(lang, T["en"])
    return table.get(key, T["en"][key]).format(**kw)


def tn(lang: str, tool: str) -> str:
    """Friendly tool name, e.g. ad_platform -> Ad platform."""
    return T.get(lang, T["en"]).get("tool_" + tool, tool)
