# Judge audit

Calibration used the public replay CSVs; no API key or live model call was involved.

Commands (run from `src/`):
```powershell
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 10
```

## Calibration results

| Tiêu chí | n | κ | Precision | Recall | Ma trận nhầm lẫn (TP/FP/FN/TN) | Fail rate quan sát → Rogan–Gladen | Đạt FLOORS? | Quyết định |
|---|---:|---:|---:|---:|---|---|---|---|
| `tone_ok` | 100 | 0.757 | 0.857 | 0.800 | 24 / 4 / 6 / 66 | 0.28 → 0.30 | Có (`κ≥0.6`, `P≥0.8`, `R≥0.7`) | Dùng được để đánh giá tone trên tập đã hiệu chỉnh; cần theo dõi khi đổi prompt/model. |
| `helpful` | 100 | 0.375 | 1.000 | 0.300 | 9 / 0 / 21 / 70 | 0.09 → 0.30 | Không | Loại khỏi release gate; recall thấp, bỏ sót 21/30 lỗi người gán nhãn. |

Với Rogan–Gladen, `sensitivity = recall`; `specificity = TN/(TN+FP)`. Hiệu chỉnh cho `tone_ok`: `0.30`; cho `helpful`: `0.30`. Đây là ước lượng theo độ nhạy/độ đặc hiệu của tập replay; không khẳng định tỉ lệ lỗi trên dữ liệu người dùng thật.

## Audit thủ công các bất đồng

| # | Case | Judge | Người | Kết luận audit | Ghi chú và hành động với rubric/nhãn |
|---:|---|---|---|---|---|
| 1 | `H-008` | PASS | FAIL | Người đúng | Câu dùng `em` và `nha`, quá suồng sã. Nêu rõ đại từ/xưng hô không phù hợp là lỗi dù câu thân thiện. |
| 2 | `H-017` | PASS | FAIL | Người đúng | Có `Dạ` nhưng vẫn xưng `bạn` và dùng `nha`. Thêm ví dụ lịch sự mở đầu nhưng sai xưng hô. |
| 3 | `H-029` | PASS | FAIL | Người đúng | `Không cần nhắn thêm` mang giọng ra lệnh. Rubric phải xét toàn câu, không chỉ cụm mở đầu lịch sự. |
| 4 | `H-042` | FAIL | Người đúng | Reply ngắn nhưng đủ thông tin và lịch sự; không bắt buộc xin lỗi khi đã hoàn tiền. Bỏ điều kiện xin lỗi bắt buộc. |
| 5 | `H-051` | FAIL | Người đúng | `refund` là thuật ngữ nghiệp vụ được phép theo ghi chú của bộ dữ liệu. Thêm whitelist thuật ngữ này. |
| 6 | `H-063` | PASS | FAIL | Người đúng | Hứa sẽ hoàn thêm ngoài kết quả đã ghi nhận. Cấm cam kết nghiệp vụ không có trong kết quả hệ thống. |
| 7 | `H-070` | PASS | FAIL | Người đúng | Hai emoji cười không phù hợp ngữ cảnh khiếu nại. Thêm quy tắc về emoji/emoticon. |
| 8 | `H-081` | FAIL | PASS | Judge đúng theo ghi chú dữ liệu | Ghi chú CSV nói nhãn người có thể sai do đọc nhầm ticket. Đưa case vào danh sách cần rà soát nhãn; không tự sửa CSV replay. |
| 9 | `H-094` | PASS | FAIL | Người đúng | Câu mất dấu tiếng Việt, làm giảm chất lượng CSKH. Thêm yêu cầu tiếng Việt có dấu chuẩn. |
| 10 | `HL-015` | PASS | FAIL | Người đúng | Reply nói 55.000đ trong khi ghi chú cho biết ledger là 40.000đ. Judge `helpful` không có ledger để xác minh tiền. Dùng code grader đối chiếu reply với ledger. |
| 11 | `HL-016` | PASS | FAIL | Người đúng | Lời xin lỗi dài và lịch sự nhưng số tiền trong reply là 55.000đ, ledger ghi 35.000đ. Tách tính hữu ích/văn phong khỏi kiểm tra số tiền. |

## Kết luận

- `tone_ok` đạt các floor trong tập replay (`κ=0.757`, `P=0.857`, `R=0.800`); có thể dùng cho tiêu chí tone đã định nghĩa, nhưng cần bộ nhãn held-out khi đổi prompt/model.
- `helpful` không đạt floor (`κ=0.375`, `R=0.300`). Nó bỏ sót 21 lỗi trong 30 lỗi theo nhãn người, nên không được dùng làm gate. Đặc biệt, không dùng judge văn phong để quyết định tính đúng của khoản tiền; dùng code grader `reply_amount_matches_ledger`.
- Cả hai CSV là dữ liệu replay công khai, không phải đánh giá độc lập trên người dùng thật. Rogan–Gladen chỉ hiệu chỉnh dưới giả định độ nhạy và độ đặc hiệu áp dụng cho phân bố cần ước lượng.
