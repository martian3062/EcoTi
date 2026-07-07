"""Bundled fraud-advisory corpus.

Public guidance paraphrased from I4C / MHA (Cyber Dost, 1930 helpline),
RBI and Sanchar Saathi, so the RAG copilot works out-of-the-box with no
Firecrawl key. When ``FIRECRAWL_API_KEY`` is set, ``ingest_advisories`` can
additionally crawl live advisory URLs and add them to the same corpus.
"""

SEED_ADVISORIES = [
    {
        "title": "Digital Arrest Scams — I4C / MHA advisory",
        "authority": "I4C",
        "url": "https://www.cybercrime.gov.in/",
        "text": (
            "No law enforcement agency in India — CBI, ED, police, customs or the "
            "Narcotics Control Bureau — ever arrests a person over a video call or "
            "demands money to 'clear' a case. 'Digital arrest' is a scam: fraudsters "
            "impersonate officials, show fake IDs and warrants, claim your Aadhaar or "
            "a parcel is linked to money laundering or drugs, and pressure you to stay "
            "on a video call in isolation while transferring money to a 'verification' "
            "or 'RBI' account. If you receive such a call: disconnect immediately, do "
            "not share OTP or transfer money, and report it on the 1930 helpline or at "
            "cybercrime.gov.in. Genuine notices are served in person or through official "
            "written channels, never by threatening video calls."
        ),
    },
    {
        "title": "Reporting financial fraud on the 1930 helpline",
        "authority": "I4C",
        "url": "https://www.cybercrime.gov.in/",
        "text": (
            "Victims of online financial fraud should call the national cyber-crime "
            "helpline 1930 as soon as possible. Fast reporting within the golden hour "
            "lets banks freeze the fraudulent transfer before the money is withdrawn. "
            "Keep the transaction ID, the fraudster's phone number or UPI handle, and "
            "any screenshots. You can also file a complaint at cybercrime.gov.in. The "
            "Citizen Financial Cyber Fraud Reporting and Management System links banks "
            "and police to trace and hold suspect funds."
        ),
    },
    {
        "title": "RBI guidance — never share OTP, PIN or card details",
        "authority": "RBI",
        "url": "https://www.rbi.org.in/",
        "text": (
            "The Reserve Bank of India and no genuine bank will ever ask for your OTP, "
            "UPI PIN, CVV, card number or net-banking password over a call, SMS, email "
            "or social media. Do not click links promising KYC updation, refunds, or "
            "reward points. Fraudsters spoof bank and RBI numbers and create fake "
            "portals. Verify only through the official bank app or branch. Report unknown "
            "debits to your bank immediately and to 1930. RBI does not maintain personal "
            "accounts for the public and never asks citizens to deposit money to 'verify'."
        ),
    },
    {
        "title": "Sanchar Saathi — report suspected fraud numbers",
        "authority": "DoT",
        "url": "https://sancharsaathi.gov.in/",
        "text": (
            "The Department of Telecommunications' Sanchar Saathi portal lets citizens "
            "report suspected fraud communication through Chakshu, block lost or stolen "
            "handsets, and check the mobile connections issued in their name. Report "
            "spoofed calls, fake KYC messages, and impersonation of officials. Blocking "
            "fraudulent numbers early disrupts scam networks that reuse the same handsets "
            "and SIMs across many victims and districts."
        ),
    },
    {
        "title": "Mule accounts and UPI fraud networks",
        "authority": "I4C",
        "url": "https://www.cybercrime.gov.in/",
        "text": (
            "Scam proceeds are laundered through 'mule' accounts — bank or UPI accounts "
            "opened with real or stolen identities and rented to fraud gangs. Money from "
            "a victim is rapidly split across many mule accounts in different districts "
            "and withdrawn, making recovery hard. Never share your bank account or UPI "
            "for someone else's transactions, even for a commission — you become legally "
            "liable. Linked clusters of mule accounts sharing devices, numbers or funding "
            "patterns are a strong signal of an organised fraud network."
        ),
    },
]
