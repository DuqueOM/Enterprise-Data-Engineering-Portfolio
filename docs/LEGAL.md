# Legal Notice & Compliance

## Overview

This document outlines legal considerations, licensing information, data usage policies, and compliance requirements for all projects in this portfolio.

---

## 📄 License Information

### Portfolio License

**MIT License** - Copyright (c) 2024

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Third-Party Licenses

This project uses various open-source libraries. See [THIRD_PARTY_LICENSES.md](./THIRD_PARTY_LICENSES.md) for complete attribution.

#### Key Dependencies

| Library | License | Usage |
|---------|---------|-------|
| FastAPI | MIT | API framework |
| scikit-learn | BSD-3-Clause | Machine learning |
| Transformers | Apache 2.0 | NLP models |
| Sentence-Transformers | Apache 2.0 | Embeddings |
| BeautifulSoup4 | MIT | Web scraping |
| Pandas | BSD-3-Clause | Data processing |
| PyTorch | BSD-3-Clause | Deep learning |
| MLflow | Apache 2.0 | Experiment tracking |

---

## 🌍 Data Usage & Privacy

### Data Collection Policy

#### What Data We Collect

**Public Web Data**
- Government websites (publicly available information)
- Official documentation and FAQs
- Regulatory compliance information
- No personal or private data

**System Logs**
- API request logs (anonymized)
- Error logs (no PII)
- Performance metrics
- Usage statistics

#### What We DON'T Collect

- ❌ Personal identifiable information (PII)
- ❌ Financial information
- ❌ Health information
- ❌ Authentication credentials
- ❌ Private user data

### Data Processing

**Legal Basis:** Legitimate interest for:
- System operation and maintenance
- Service improvement
- Security and fraud prevention
- Compliance with legal obligations

**Data Retention:**
```yaml
Retention Periods:
  - Raw scraped data: 90 days
  - Processed datasets: 1 year
  - Model artifacts: 2 years
  - System logs: 30 days
  - Audit logs: 7 years (compliance)
```

### PII Sanitization

All data undergoes automated PII detection and removal:

```python
"""
Automated PII patterns detected and removed:
- Email addresses
- Phone numbers
- Social security numbers
- Credit card numbers
- National ID numbers
- IP addresses (when not essential)
"""
```

**Compliance:** GDPR Art. 32 (Security of Processing)

---

## 🔒 User Rights (GDPR/CCPA)

### Right to Access
Users can request access to any data collected about them.

**Process:**
1. Submit request via email: privacy@example.com
2. Identity verification required
3. Response within 30 days
4. Data provided in machine-readable format (JSON)

### Right to Erasure (Right to be Forgotten)
Users can request deletion of their data.

**Process:**
1. Submit deletion request
2. Verify identity
3. Delete data within 30 days
4. Provide confirmation

**Exceptions:**
- Legal obligations require retention
- Public interest/research purposes (anonymized)

### Right to Rectification
Users can request correction of inaccurate data.

### Right to Data Portability
Users can export their data in standard formats.

---

## ⚖️ Terms of Service

### Acceptable Use Policy

#### ✅ Permitted Uses
- Academic research and education
- Personal projects and learning
- Commercial use with attribution
- Derivative works (with same license)

#### ❌ Prohibited Uses
- Malicious activities (hacking, DDoS)
- Copyright infringement
- Unauthorized data mining at scale
- Circumventing security measures
- Impersonation or fraud
- Violation of applicable laws

### Service Limitations

**Disclaimer:**
```
THIS SOFTWARE IS PROVIDED FOR DEMONSTRATION AND EDUCATIONAL PURPOSES.
IT IS NOT INTENDED FOR PRODUCTION USE WITHOUT PROPER REVIEW, TESTING,
AND COMPLIANCE VERIFICATION FOR YOUR SPECIFIC USE CASE.
```

**No Warranty:**
- Software provided "as is"
- No guarantee of accuracy or reliability
- Use at your own risk
- Authors not liable for damages

---

## 🌐 Web Scraping Compliance

### Ethical Scraping Practices

#### Robots.txt Compliance
```python
"""
All scrapers respect robots.txt directives:
- Check robots.txt before scraping
- Honor crawl-delay directives
- Respect disallowed paths
"""

from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://example.com/robots.txt")
rp.read()

if rp.can_fetch("*", url):
    # Proceed with scraping
    pass
```

#### Rate Limiting
```python
"""
Implemented rate limits to avoid server overload:
- Max 1 request per 2 seconds per domain
- Exponential backoff on errors
- Respect 429 (Too Many Requests) responses
"""
```

#### User-Agent Identification
```python
"""
Transparent identification in requests:
User-Agent: MLOps-Portfolio-Bot/1.0 
            (+https://github.com/yourusername/portfolio; 
            contact@example.com)
"""
```

### Legal Considerations

**Public Data Only:**
- Only scrape publicly accessible content
- No authentication bypass
- No paywalled content
- Respect copyright and terms of service

**Fair Use Assessment:**
- Transformative use (ML training)
- Non-commercial (portfolio/education)
- Limited data quantity
- No market harm

---

## 📊 Model & Dataset Licensing

### Dataset Distribution

When publishing datasets derived from this project:

**Required Attribution:**
```
Data sourced from [Source Name]
Processed using MLOps Portfolio Tools
Original data: [Original URL]
License: [Specify based on source]
```

**Recommended Licenses:**
- **CC BY 4.0**: Allows commercial use with attribution
- **CC BY-SA 4.0**: Share-alike, copyleft protection
- **CC0**: Public domain dedication

### Model Licensing

Models trained on public data:

**License:** MIT (for model architecture/code)

**Model Card Requirements:**
```markdown
# Model Card

## Model Details
- Model type: [e.g., Logistic Regression, BERT]
- Version: [v1.0.0]
- Date: [2024-01-15]

## Intended Use
- Primary use: [Q&A retrieval for administrative queries]
- Out-of-scope: [Medical advice, financial guidance]

## Training Data
- Source: [Publicly available government FAQs]
- Size: [10,000 Q&A pairs]
- Language: [Spanish]

## Ethical Considerations
- Bias assessment: [Describe any known biases]
- Limitations: [Performance drops on out-of-domain queries]

## Citation
[Provide citation format]
```

---

## 🏛️ Regulatory Compliance

### GDPR (EU General Data Protection Regulation)

**Compliance Measures:**
- ✅ Data minimization (Art. 5)
- ✅ Purpose limitation (Art. 5)
- ✅ Storage limitation (Art. 5)
- ✅ Security measures (Art. 32)
- ✅ Data breach notification (Art. 33)
- ✅ Data protection by design (Art. 25)

**Data Processing Agreement (DPA):**
Available upon request for enterprise deployments.

### CCPA (California Consumer Privacy Act)

**Consumer Rights:**
- ✅ Right to know what data is collected
- ✅ Right to delete personal information
- ✅ Right to opt-out of data sales (N/A - we don't sell data)
- ✅ Right to non-discrimination

### HIPAA (If Applicable)

**⚠️ Important:** This system is **NOT HIPAA-compliant** by default.

Do not process Protected Health Information (PHI) without:
- Business Associate Agreement (BAA)
- Additional security controls
- Audit logging for PHI access
- Encryption at rest and in transit

---

## 📝 Intellectual Property

### Copyright

**Original Work:** All original code, documentation, and configurations are copyrighted.

**Copyright Notice:**
```
Copyright (c) 2024 [Your Name/Organization]
All rights reserved except as expressly granted by license.
```

### Trademarks

No trademarks are claimed. Third-party trademarks mentioned are property of their respective owners.

### Patents

No patent claims. Open-source contributions welcome.

---

## 🤝 Contributor License Agreement (CLA)

### For Contributors

By contributing to this project, you agree:

1. **Grant of License:** You grant a perpetual, worldwide, non-exclusive license to use your contributions under the project's MIT license.

2. **Original Work:** Your contributions are your original work or you have rights to submit them.

3. **No Obligations:** You are not bound by any agreements that conflict with this contribution.

4. **Warranty:** You provide contributions "as is" without warranties.

---

## 📞 Contact Information

### Legal Inquiries

**Privacy Questions:**  
privacy@example.com

**Licensing Questions:**  
legal@example.com

**Security Reports:**  
security@example.com (PGP key available)

**General Contact:**  
contact@example.com

### Reporting Violations

If you believe content violates:
- Copyright (DMCA takedown)
- Privacy rights
- Terms of service

Contact: legal@example.com with:
- Description of violation
- Location of content
- Your contact information
- Good faith statement

**Response Time:** Within 5 business days

---

## 📅 Updates & Changes

### Change Log

**Version 1.0** (2024-01-15)
- Initial legal framework
- GDPR/CCPA compliance measures
- PII sanitization policies

### Review Schedule

This document is reviewed:
- **Quarterly:** Compliance updates
- **Annually:** Comprehensive legal review
- **As Needed:** Regulatory changes

---

## 📚 Additional Resources

### Legal Frameworks
- [GDPR Official Text](https://gdpr-info.eu/)
- [CCPA Official Text](https://oag.ca.gov/privacy/ccpa)
- [Open Source Initiative](https://opensource.org/)

### Best Practices
- [Google's ML Fairness](https://developers.google.com/machine-learning/fairness-overview)
- [Microsoft's Responsible AI](https://www.microsoft.com/en-us/ai/responsible-ai)
- [Partnership on AI](https://partnershiponai.org/)

---

## ⚠️ Disclaimers

### No Legal Advice

This document is informational only and does not constitute legal advice. Consult qualified legal counsel for specific situations.

### No Endorsement

Mention of third-party products, services, or organizations does not imply endorsement.

### Limitation of Liability

```
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

---

**Document Version:** 1.0  
**Effective Date:** 2024-01-15  
**Last Reviewed:** 2024-01-15  
**Next Review:** 2024-04-15
