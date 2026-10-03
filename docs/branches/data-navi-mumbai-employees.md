# Employee data foundation

Owns app/employees/data.py, import command and tests. Imports Employee_Master/Store_Staffing atomically into indexed employees and staffing tables linked to shared stores. Source full names are not assumed unique. Unicode/apostrophe-normalized search names are indexed. Optional performance ratings remain null; invalid percentages/ratings/IDs/store links and headcount mismatches reject the batch. Reimports are hash-idempotent.

Actual workbook: 150 employees, 20 staffing rows, 19 missing performance ratings. Supplied data is synthetic, remains local and is not committed. Nullable/atomicity/name normalization regression passed. API access control and UI are downstream gates.
