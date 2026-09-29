# Requirements

## Business Context

This system supports EPAM India overtime eligibility, compensation calculation, request tracking, and submission based on the Overtime Compensation Policy and the 17 human-approved clarifications recorded during review.

The updated eligibility and compensation rules are effective 1 August 2026 (Source Policy).

## Actors

- Associate
- Delivery Manager / Delivery Head
- Project Sponsor
- Account Manager
- Ask Compensation team
- TA Operations team
- HRBP
- PMO office
- HR Team / policy governance stakeholders

## Requirement Classifications

- **Source Policy**: Directly stated in the supplied Overtime Compensation Policy outside its FAQ.
- **Source FAQ**: Stated in the FAQ portion of the supplied policy export.
- **Human-Approved Clarification**: Explicitly approved during this review conversation and authoritative for this system.
- **System Decision**: System behavior approved during this review conversation where the source policy is silent or ambiguous.
- **Not Found**: The source policy and approved clarifications do not define the value or behavior.
- **Out of Scope**: Present in the source policy but outside this system's overtime eligibility, calculation, tracking, and submission scope.

## Functional Requirements

- **FR-001** (System Decision): Capture associate identifier, employment category, project code, overtime date, overtime hours, working-day classification, project-designated working hours, required wage data, calculated hourly wage, applicable scenario, calculated compensation, compensatory-off eligibility, Delivery Manager or Delivery Head, Project Sponsor, Account Manager, approval status, approval evidence/reference, submission date, and processing status.
- **FR-002** (System Decision): Any additional mandatory field not defined by the policy shall be recorded as `Not Found` and shall not be invented.
- **FR-003** (Human-Approved Clarification): Eligibility is limited to production-category full-time, part-time, and subcontractor associates when overtime is requested by the business and approved in advance.
- **FR-004** (Human-Approved Clarification): Overtime not requested by the business and approved in advance is not eligible for compensation. The automatic disposition of unauthorized overtime is `Not Found`.
- **FR-005** (Human-Approved Clarification): Record actual working hours excluding the included lunch break.
- **FR-006** (Human-Approved Clarification): Use the project-designated working calendar to classify working and non-working days, accounting for project-specific schedules, weekends, and applicable public holidays.
- **FR-007** (Human-Approved Clarification): Project configuration shall explicitly define the weekly start day and time zone.
- **FR-008** (Human-Approved Clarification): Project-designated working hours shall accept exactly 8 or 9. Any other value is invalid configuration; a missing value is `Not Found`. Both conditions block compensation calculation.
- **FR-009** (Human-Approved Clarification): Missing project calendar, weekly start day, or time zone shall be reported as `Not Found` and block eligibility evaluation until human configuration is provided.
- **FR-010** (Human-Approved Clarification): Evaluate the 48-hour threshold using actual working hours excluding lunch, within configured weekly start and end boundaries and time zone.
- **FR-011** (Human-Approved Clarification): Exactly 48 actual working hours creates no overtime eligibility. Only approved overtime hours beyond 48 actual working hours are eligible.
- **FR-012** (Human-Approved Clarification): The Delivery Manager or Delivery Head initiates and coordinates the overtime request.
- **FR-013** (Human-Approved Clarification): Prior approval must be obtained from both the Project Sponsor and Account Manager before overtime is worked.
- **FR-014** (Human-Approved Clarification): Only overtime with required advance business approval is eligible for compensation.
- **FR-015** (Human-Approved Clarification): Roles mentioned in the source policy are not additional mandatory approvers unless explicitly required by an approved clarification.
- **FR-016** (System Decision): Retain approval evidence or a reference to that evidence.
- **FR-017** (Source Policy): Wage Salary consists of Basic Salary plus Special Allowance.
- **FR-018** (Human-Approved Clarification): The authoritative hourly wage formula is `Hourly wage = Wage Salary / 365 / project-designated working hours`.
- **FR-019** (Human-Approved Clarification): If the project designates 8 working hours, use 8; if it designates 9 working hours, use 9.
- **FR-020** (Human-Approved Clarification): If required wage data is unavailable, mark it `Not Found`, block calculation and processing, direct the Delivery Manager to the HRBP, and resume only after data is provided and validated.
- **FR-021** (Human-Approved Clarification): Do not estimate, infer, or use a fallback wage value.
- **FR-022** (Human-Approved Clarification): Retain full precision for fractional overtime hours and perform no intermediate rounding.
- **FR-023** (Human-Approved Clarification): Round the final monetary compensation amount to 2 decimal places in INR.
- **FR-024** (Source Policy): Overtime pay is taxable with the associate's monthly pay.
- **FR-025** (Human-Approved Clarification): Approved overtime during a working day is compensated at 2 times the hourly wage rate.
- **FR-026** (Human-Approved Clarification): Approved overtime during a non-working day of less than 6 actual working hours is not eligible for overtime compensation.
- **FR-027** (Human-Approved Clarification): Approved overtime during a non-working day from 6 to less than 9 actual working hours is compensated at 2 times the hourly wage rate.
- **FR-028** (Human-Approved Clarification): Approved overtime during a non-working day of 9 or more actual working hours receives 1 times the hourly wage rate plus 1 compensatory off.
- **FR-029** (Human-Approved Clarification): For the 9-or-more-hour non-working-day scenario, compensatory off must be applied for within 30 days of qualifying overtime, utilized within 90 days, and remain subject to applicable business requirement and approval.
- **FR-030** (Source Policy): Tag overtime payout to the relevant project code.
- **FR-031** (Human-Approved Clarification): Record or register overtime hours within 15 days of the date worked.
- **FR-032** (Human-Approved Clarification): Update the overtime time report before the 5th of the following month to support timely payment processing.
- **FR-033** (System Decision): Track the submission date and processing status where possible.
- **FR-034** (Source Policy): Submit regular-employee approved overtime calculations and approval evidence to Ask Compensation at `AskCompensation@epam.com`.
- **FR-035** (Human-Approved Clarification): Submit subcontractor approved overtime payment details to TA Operations at `WFATAReportingAndAnalyticsIndia@epam.com`.
- **FR-036** (System Decision): Support `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `RETURNED`, `READY_FOR_PROCESSING`, `SUBMITTED`, `PAID`, and `FAILED`.
- **FR-037** (System Decision): Retain status history and audit information where applicable.
- **FR-038** (System Decision): Treat workflow statuses as system statuses and do not represent them as Source Policy statuses unless explicitly supported by the policy.
- **FR-039** (Not Found): The source policy does not define the payment confirmation source or evidence required to set `PAID` or `FAILED`.

## Non-Functional Requirements

- **NFR-001** (System Decision): Each calculated result retains its inputs, scenario, approval evidence, submission date, processing status, and status history where applicable.
- **NFR-002** (System Decision): Fail closed when required calendar configuration, approval, or wage data is missing; do not silently assume defaults.
- **NFR-003** (System Decision): Preserve calculation precision until final INR rounding.
- **NFR-004** (System Decision): Protect wage data, associate identifiers, approval evidence, and contact information from unauthorized disclosure. Specific access-control requirements are `Not Found`.
- **NFR-005** (System Decision): Distinguish source-policy wording from human-approved system decisions.

## Business Rules

- **BR-001** (Source Policy): The policy covers production-category full-time, part-time, and subcontractor associates.
- **BR-002** (Source Policy): The standard business day is 9 hours including a 1-hour lunch break.
- **BR-003** (Source Policy): Associates are encouraged to take breaks and not work more than 4 hours without a break.
- **BR-004** (Source Policy): Female associates can avail home-drop support after 8 PM subject to the transport policy.
- **BR-005** (Source Policy): Associates working under the Shift Allowance Policy are within the policy scope.
- **BR-006** (Source Policy): Overtime may be based on mutual agreement between the associate and the business.
- **BR-007** (Source Policy): Additional project-related compensation or expenses are chargeable to the respective account subject to applicable approvals.
- **BR-008** (Source Policy): Policy amendments, suspension, or withdrawal are announced by the HR Team.
- **BR-009** (Source Policy): Overtime pay is taxable with monthly pay.

## Eligibility Rules

- Working-day approved overtime is `2X` (Human-Approved Clarification).
- Non-working-day approved overtime below 6 actual working hours is ineligible (Human-Approved Clarification).
- Non-working-day approved overtime from 6 to less than 9 actual working hours is `2X` (Human-Approved Clarification).
- Non-working-day approved overtime of 9 or more actual working hours is `1X + 1 compensatory off` (Human-Approved Clarification).
- Production-category full-time, part-time, and subcontractor associates are eligible when overtime is business-requested and approved in advance (Human-Approved Clarification).

## Approval Workflow

The Delivery Manager or Delivery Head initiates and coordinates the request. Prior approval from both the Project Sponsor and Account Manager is required before overtime is worked (Human-Approved Clarification). Other roles are not additional mandatory approvers unless explicitly required by an approved clarification (Human-Approved Clarification).

## Compensation Rules

- Wage Salary is Basic Salary plus Special Allowance (Source Policy).
- Working-day approved overtime is `2X` (Human-Approved Clarification).
- Non-working-day approved overtime uses the 6-hour and 9-hour bands in FR-026 through FR-028 (Human-Approved Clarification).
- Overtime payout is tagged to the project code (Source Policy).

## Calculation Rules

- `Hourly wage = Wage Salary / 365 / project-designated working hours` (Human-Approved Clarification).
- Project-designated working hours are 8 or 9 only; invalid or missing configuration blocks calculation (Human-Approved Clarification).
- Fractional hours retain full precision, with no intermediate rounding; final INR is rounded to 2 decimals (Human-Approved Clarification).
- Exactly 48 actual working hours creates no eligibility; only hours beyond 48 qualify within configured weekly boundaries and time zone, with lunch excluded (Human-Approved Clarification).

## Compensatory Off Rules

For approved non-working-day overtime of 9 or more actual working hours, the associate receives 1X compensation plus 1 compensatory off. The compensatory off must be applied for within 30 days, utilized within 90 days, and remains subject to business requirement and approval (Human-Approved Clarification).

## Time Reporting

Both requirements apply (Human-Approved Clarification): overtime must be registered within 15 days of the overtime date, and the time report must be updated before the 5th of the following month.

## Inputs

- Associate identifier and employment category
- Project code and project configuration
- Project-designated working calendar
- Configured weekly start day and time zone
- Overtime date and actual working hours
- Project-designated working hours
- Wage Salary data
- Delivery Manager or Delivery Head details
- Project Sponsor and Account Manager details
- Advance approval evidence or reference
- Overtime registration and time-report dates
- Processing-team submission data and status updates

## Outputs

- Eligibility result
- `Not Found` missing-data or configuration result
- Weekly hours used for threshold evaluation
- Hourly wage calculation
- Applicable overtime scenario
- INR compensation rounded to 2 decimal places
- Compensatory-off eligibility and deadlines
- Project-code assignment
- Approval status and evidence reference
- Submission date
- Processing status and status history
- HRBP escalation instruction for missing wage data
- Responsible processing-team destination

## Workflow Statuses

The supported system statuses are `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `RETURNED`, `READY_FOR_PROCESSING`, `SUBMITTED`, `PAID`, and `FAILED` (System Decision). Status history and audit information are retained where applicable (System Decision). Status transition rules and transition authorization are `Not Found` because the source policy does not define authoritative transition rules. No transition behavior is invented by the system requirements (System Decision).

## Error Scenarios

- **ES-001** (Not Found): Missing project calendar blocks eligibility evaluation.
- **ES-002** (Not Found): Missing weekly start day blocks weekly threshold evaluation.
- **ES-003** (Not Found): Missing time zone blocks weekly threshold evaluation.
- **ES-004** (Human-Approved Clarification): Missing wage data is `Not Found`, blocks calculation and processing, and directs the Delivery Manager to the HRBP.
- **ES-005** (Not Found): Missing approval evidence prevents the request from being treated as approved or eligible. The automatic disposition is `Not Found`.
- **ES-006** (Human-Approved Clarification): Overtime not requested by the business is marked not eligible for compensation.
- **ES-007** (Human-Approved Clarification): Non-working-day overtime below 6 actual working hours is not eligible.
- **ES-008** (Not Found): Invalid project-designated working hours block compensation calculation.
- **ES-009** (Not Found): Missing project-designated working hours are reported as `Not Found` and block compensation calculation.
- **ES-010** (Human-Approved Clarification): Both reporting requirements apply: overtime must be registered within 15 days of the overtime date, and the time report must be updated before the 5th of the following month. Consequences beyond these requirements are `Not Found`.
- **ES-011** (Not Found): Payment confirmation evidence and the payment-processing SLA are not defined by the source policy.
- **ES-012** (System Decision): A conflicting subcontractor FAQ contact is flagged while processing uses `WFATAReportingAndAnalyticsIndia@epam.com`.

## Acceptance Criteria

1. A production-category full-time, part-time, or subcontractor associate with business-requested, advance-approved overtime can be evaluated.
2. Overtime without required advance approval is not eligible, and its automatic disposition is `Not Found`.
3. Missing calendar, weekly start day, time zone, or wage data is reported as `Not Found` and blocks the relevant evaluation or calculation.
4. Project working hours of 8 and 9 are accepted; any other value is invalid and a missing value is `Not Found`; both block calculation.
5. Exactly 48 actual working hours creates no overtime eligibility.
6. Only approved hours beyond 48 actual working hours qualify, using configured weekly start/end boundaries and time zone.
7. Actual working hours exclude the included lunch break.
8. Working-day approved overtime calculates at 2X.
9. Non-working-day approved overtime below 6 actual working hours is not eligible.
10. Non-working-day approved overtime from 6 to less than 9 actual working hours calculates at 2X.
11. Non-working-day approved overtime of 9 or more actual working hours calculates at 1X and grants compensatory-off eligibility.
12. Compensatory off is applied for within 30 days, utilized within 90 days, and remains subject to business approval.
13. Fractional hours are not rounded during calculation and final INR compensation is rounded to 2 decimal places.
14. Overtime is registered within 15 days and the time report is updated before the 5th of the following month; both requirements are tracked for their separate purposes.
15. Regular-employee submissions route to Ask Compensation and subcontractor submissions route to TA Operations at `WFATAReportingAndAnalyticsIndia@epam.com`.
16. Invalid working hours block calculation.
17. Missing approval evidence prevents the request from being treated as approved or eligible, and its automatic disposition is `Not Found`.
18. Missing wage data blocks processing, directs the Delivery Manager to the HRBP, and uses no fallback wage.
19. Supported workflow statuses and status history are tested.
20. Status transition rules are `Not Found` because the source policy does not define authoritative transition rules.
21. No transition behavior is invented by the system requirements.
22. Payment confirmation evidence for `PAID` and `FAILED` is `Not Found`.
23. The payment-processing SLA remains `Not Found`.
24. Policy-level exception authority remains `Not Found`.
25. The conflicting subcontractor FAQ contact is retained in the documentation inconsistency register and flagged for review.
26. Documentation inconsistencies are recorded and not silently removed.

## Assumptions

- No business assumptions are added beyond the human-approved clarifications.
- Payment-processing SLA, payment confirmation evidence, policy-level exception authority, additional mandatory fields, workflow transition rules, and consequences for missed reporting requirements are `Not Found`.

## Open Questions / Not Found

- Payment-processing or payment deadline after submission: `Not Found`.
- Payment confirmation source/evidence for `PAID` or `FAILED`: `Not Found`.
- Policy-level exception approval authority: `Not Found`; this is distinct from normal overtime-request approval.
- Automatic disposition for missed reporting requirements: `Not Found`.
- Additional mandatory fields not defined by the policy: `Not Found`.
- Required access-control model: `Not Found`.
- Workflow transition rules and transition authorization: `Not Found`.

## Traceability Matrix

| Requirement area | Final identifier(s) | Primary classification | Authority |
|---|---|---|---|
| Request capture and missing fields | FR-001, FR-002 | System Decision | Approved capture set; undefined additional fields are `Not Found`. |
| Eligibility scope | FR-003, FR-004, FR-005 | Human-Approved Clarification | Policy section 3 and clarification decision 4; lunch treatment is clarification decision 8. |
| Calendar and weekly threshold | FR-006, FR-007, FR-008, FR-009, FR-010, FR-011 | Human-Approved Clarification | Source policy section 4 and clarification decisions 8 and 16. |
| Approval workflow | FR-012, FR-013, FR-014, FR-015, FR-016 | Human-Approved Clarification | Clarification decision 3. |
| Wage components | FR-017 | Source Policy | Policy definitions. |
| Hourly wage formula | FR-018, FR-019 | Human-Approved Clarification | Clarification decision 2 supersedes the conflicting source formula. |
| Missing wage data | FR-020, FR-021 | Human-Approved Clarification | Clarification decision 17. |
| Precision and rounding | FR-022, FR-023 | Human-Approved Clarification | Clarification decision 9. |
| Taxability | FR-024 | Source Policy | Policy section 5 note. |
| Compensation scenarios | FR-025, FR-026, FR-027, FR-028, FR-029, FR-030 | Human-Approved Clarification | Clarification decisions 1 and 15; policy section 5 supplies scenario context. |
| Time reporting | FR-031, FR-032, FR-033 | Human-Approved Clarification | Clarification decision 5. |
| Processing contacts | FR-034, FR-035 | Human-Approved Clarification | Clarification decision 7 and policy procedure. |
| Workflow statuses and history | FR-036, FR-037, FR-038 | System Decision | Clarification decision 14; statuses are not source-policy statuses. |
| Payment confirmation evidence | FR-039 | Not Found | Not defined by the source policy. |
| Non-functional controls | NFR-001, NFR-002, NFR-003, NFR-004, NFR-005 | System Decision | System behavior; specific access-control requirements are `Not Found`. |
| Policy source statements | BR-001, BR-002, BR-003, BR-004, BR-005, BR-006, BR-007, BR-008, BR-009 | Source Policy | Source policy scope, guidance, mutual consent, charging, taxability, and governance statements. |

## Conflict / Documentation Inconsistency Register

1. **Hourly wage formula:** Source Policy contains conflicting formulas. Human-Approved Clarification 2 makes `Wage Salary / 365 / project-designated working hours` authoritative.
2. **6-hour threshold:** The minimum appears in the Source FAQ but not explicitly in the scenario table. Human-Approved Clarification 15 makes it authoritative.
3. **Subcontractor contact:** The procedure contact `WFATAReportingAndAnalyticsIndia@epam.com` is authoritative under Human-Approved Clarification 7. The conflicting FAQ contact is retained and flagged for review.
4. **Lunch-break treatment:** Source Policy defines a 9-hour day including lunch but does not define lunch treatment for the 48-hour threshold. Human-Approved Clarification 8 excludes lunch from actual working hours.
5. **Other clarified rules:** Approval, eligibility, compensatory-off timelines, reporting purposes, calendar authority, weekly boundaries, precision, rounding, statuses, and HRBP escalation are classified as Human-Approved Clarification or System Decision in the relevant requirements.

## Out of Scope

- **OS-001** (Out of Scope): Break monitoring and enforcement beyond recording actual working hours.
- **OS-002** (Out of Scope): Home-drop and transport eligibility or processing.
- **OS-003** (Out of Scope): Separate Shift Allowance calculation and processing. The Shift Allowance scope statement remains BR-005 (Source Policy).
- **OS-004** (Out of Scope): Determining mutual consent between associate and business.
- **OS-005** (Out of Scope): Processing additional project-related compensation, expenses, or account charging beyond tagging overtime payout to the project code.
- **OS-006** (Out of Scope): Selecting discretionary compensation options outside the clarified scenario rules; any undefined option is `Not Found`.
- **OS-007** (Out of Scope): HR policy amendment, suspension, withdrawal, and policy-level governance. Policy-exception authority is `Not Found`.
