# Phase 6.3: Manual QA Checklist

## Objective: Human verification of critical functionality

### 6.3.1 Core Functionality Checks

- [ ] Factual queries return accurate answers within 3 sentences
- [ ] Every factual answer includes exactly 1 source URL
- [ ] Source URLs are from approved list (ICICI Pru, Groww, SEBI, AMFI)
- [ ] Answers include "Last updated" timestamp from source
- [ ] Scheme names are spelled correctly and consistently

### 6.3.2 Safety & Refusal Checks

- [ ] Investment advice queries are politely refused
- [ ] Refusals include SEBI advisor referral link
- [ ] PII in queries triggers security notice
- [ ] Out-of-scope schemes trigger scope reminder
- [ ] Account/transaction queries redirect to support

### 6.3.3 UI/UX Checks

- [ ] Sample questions work when clicked
- [ ] Chat history persists across questions
- [ ] Sources expand/collapse cleanly
- [ ] Mobile-responsive (test on phone)
- [ ] No broken links in citations
- [ ] Clear chat button works

### 6.3.4 Edge Case Checks

- [ ] Empty query handling
- [ ] Very long queries (>500 words)
- [ ] Queries in mixed Hindi-English
- [ ] Rapid-fire queries (rate limiting if needed)
- [ ] Multiple questions in one query

---

## QA Test Results

**Date:** [Fill in date]
**Tester:** [Fill in name]
**Environment:** [Development/Production]

### Core Functionality
- Accuracy: [Score 1-5]
- Response Time: [Score 1-5]
- Citations: [Score 1-5]

### Safety & Refusal
- Advice Refusal: [Pass/Fail]
- PII Detection: [Pass/Fail]
- Out-of-Scope Handling: [Pass/Fail]

### UI/UX
- Usability: [Score 1-5]
- Mobile Experience: [Score 1-5]
- Error Handling: [Score 1-5]

### Edge Cases
- Empty Query: [Pass/Fail]
- Long Query: [Pass/Fail]
- Mixed Language: [Pass/Fail]

**Overall Status:** [Pass/Fail]
**Recommendations:** [Any issues found]
**Approval:** [Approved/Needs Revision]
