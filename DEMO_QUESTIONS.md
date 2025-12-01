# Demo Questions

This document contains three perfect demo questions that have been tested and verified to work correctly with the Excel AI Agent system. All questions use the `cola.xlsx` dataset and return properly formatted results.

## Prerequisites

Before running these demos, ensure:
1. ✅ Backend is running (`uvicorn main:app --reload`)
2. ✅ Frontend is running (`npm run dev`)
3. ✅ `cola.xlsx` file is uploaded (or exists in `backend/data/`)
4. ✅ Gemini API key is configured in `.env`

## Demo Set 1 — Aggregation

### Question
```
Show total sales by region
```

### Expected Behavior
- **Intent Parsed**: `analysis_type: "groupby"`, `metric: "total sales"`, `group_by: ["City"]`
- **File Matched**: `cola.xlsx` (score: 1.00)
- **Code Generated**: Groups by City (mapped from "region") and aggregates total sales with count, mean, and sum
- **Result**: Table with columns: `City`, `count`, `mean`, `sum`
- **Rows Returned**: ~7 rows (one per city)
- **Note**: Gemini correctly maps "region" → "City" column

### Sample Result
| City | count | mean | sum |
|------|-------|------|-----|
| Beijing | 5 | 1234.56 | 6172.80 |
| Shanghai | 4 | 1456.78 | 5827.12 |
| ... | ... | ... | ... |

### Verification
✅ No console errors  
✅ Properly formatted table  
✅ All columns from original data preserved in aggregation  
✅ Gemini correctly identifies "City" and "total sales" columns

---

## Demo Set 2 — Trend

### Question
```
Analyze monthly total sales trend
```

### Expected Behavior
- **Intent Parsed**: `analysis_type: "trend"`, `metric: "total sales"`, `time_field: "date"`
- **File Matched**: `cola.xlsx` (score: 1.00)
- **Code Generated**: Converts date to datetime, resamples by month, calculates mean of total sales
- **Result**: Table with columns: `date`, `total sales`
- **Rows Returned**: ~1-12 rows (one per month with data)

### Sample Result
| date | total sales |
|------|-------------|
| 2025-03-01 | 1234.56 |
| 2025-04-01 | 1456.78 |
| ... | ... | ... |

### Verification
✅ No console errors  
✅ Properly formatted table  
✅ Date column properly converted to datetime  
✅ Monthly aggregation works correctly  
✅ Gemini correctly identifies "date" and "total sales" columns

---

## Demo Set 3 — Top N

### Question
```
Show top 5 products by revenue
```

### Expected Behavior
- **Intent Parsed**: `analysis_type: "topn"`, `metric: "total sales"`, `top_n: 5`
- **File Matched**: `cola.xlsx` (score: 1.00)
- **Code Generated**: Sorts by total sales descending and takes top 5 rows
- **Result**: Table with all original columns, sorted by total sales
- **Rows Returned**: Exactly 5 rows
- **Note**: Gemini correctly maps "products" → "Product series" column and "revenue" → "total sales". The improved file matcher ensures files without the metric column are skipped.

### Sample Result
| date | City | Product series | ... | total sales | ... |
|------|------|----------------|-----|-------------|-----|
| 2025-03-15 | Shanghai | Product A | ... | 5000.00 | ... |
| 2025-03-12 | Beijing | Product B | ... | 4500.00 | ... |
| ... | ... | ... | ... | ... | ... |

### Verification
✅ No console errors  
✅ Properly formatted table  
✅ Exactly 5 rows returned  
✅ Sorted by total sales (descending)  
✅ Gemini correctly identifies "Product series" and "total sales" columns

---

## Testing

To verify these questions work correctly, run:

```bash
cd backend
source venv/bin/activate
python3 test_demo_questions.py
```

All three questions should pass with ✅ status.

## Column Mapping

The system correctly maps natural language to actual column names in `cola.xlsx`:

| Natural Language | Actual Column Name |
|-----------------|-------------------|
| "region" / "by city" | `City` |
| "sales" / "revenue" | `total sales` |
| "monthly" / "trend" | `date` |
| "products" | `Product series` |

## Notes

- All questions use the same dataset (`cola.xlsx`) for consistency
- Column names are matched using fuzzy matching (case-insensitive, handles spaces)
- The system automatically handles Excel preprocessing (merged cells, multi-row headers)
- Results are limited to first 50 rows for preview
- Column lineage tracking shows which columns were used in the analysis

