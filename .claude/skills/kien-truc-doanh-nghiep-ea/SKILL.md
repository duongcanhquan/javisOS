---
name: Kiến trúc doanh nghiệp & Thẩm định hệ thống
description: "Thẩm định kiến trúc CNTT enterprise, 4 mô hình hoạt động (Operating Model), 4 nấc thang trưởng thành và chuẩn đối soát 80 bảng LMS."
description_en: "Enterprise Architecture assessment, 4 Operating Models, architecture maturity stages, and 80-table LMS benchmark."
group: AI & Hệ thống
---

# Kiến Trúc Doanh Nghiệp & Thẩm Định Hệ Thống (Ross, Weill & APC Blueprint)

## Giới thiệu & Tác dụng của Skill

### 1. Vấn đề thực tế cần giải quyết
- Rất nhiều tổ chức giáo dục và doanh nghiệp rơi vào cái bẫy **"chuyển đổi số chắp vá" (vibe coding, silo ứng dụng)**: mỗi phòng ban tự mua hoặc code một phần mềm riêng, dữ liệu nằm rải rác, không liên thông, dẫn đến các báo cáo số liệu mâu thuẫn nhau giữa Phòng Đào tạo, Kế toán và Tuyển sinh.
- Nguy hiểm hơn, nhiều đơn vị bị thuyết phục chuyển sang các nền tảng dùng chung bên ngoài (multi-tenant shared server) nhưng thiếu cơ chế cô lập dữ liệu (Tenant Isolation), tạo ra rủi ro rò rỉ dữ liệu học viên và đánh mất quyền tự chủ công nghệ của nhà trường.

### 2. Tác dụng cốt lõi của Skill này
- **Cung cấp thước đo thẩm định công nghệ chuẩn mực:** Định hình rõ kiến trúc doanh nghiệp (EA) là bài toán chiến lược quản trị của Ban Giám hiệu, không phải là việc kỹ thuật thuần túy của bộ phận IT.
- **Xác định đúng Mô hình hoạt động (Operating Model):** Giúp tổ chức định vị rõ mức độ chuẩn hóa quy trình và mức độ tích hợp dữ liệu cần thiết (mô hình Hợp nhất vs Phối hợp) để đầu tư công nghệ trúng đích.
- **Bộ công cụ đối soát 80 bảng Enterprise LMS:** Dùng bản thiết kế chuẩn 80 bảng và 5 Domain cốt lõi của APC làm thước đo đối soát với mọi nhà cung cấp phần mềm, ngăn chặn hoàn toàn việc mua phải phần mềm kém chất lượng.
- **Bảo vệ chủ quyền dữ liệu số:** Đưa ra các tiêu chí kiểm tra nghiêm ngặt về phân quyền ma trận RBAC, cơ chế cô lập dữ liệu (Tenant Isolation) và khả năng xuất/nhập dữ liệu độc lập qua API.

## Khi nào dùng
- Khi thẩm định, đánh giá và đối soát các đề xuất phần mềm quản trị trường học (như so sánh UMS và CIS).
- Khi thiết kế spec kỹ thuật, sơ đồ ERD hoặc luồng dữ liệu cho các dự án chuyển đổi số mới.
- Khi tham mưu cho Ban Giám hiệu về chiến lược CNTT, quy hoạch dữ liệu tổng thể và lộ trình đầu tư phần mềm.
- Khi phản biện các đề xuất kỹ thuật chắp vá, thiếu căn cứ kiến trúc từ các đơn vị liên kết hoặc nhà thầu công nghệ.

## Nguồn tri thức nền tảng
- **Chiến Lược Kiến Trúc Doanh Nghiệp (Enterprise Architecture as Strategy)** - Jeanne W. Ross, Peter Weill (Giám đốc Trung tâm Nghiên cứu Hệ thống Thông tin MIT CISR) & David C. Robertson.
- **System Architecture Blueprint - LMS Việt Mỹ (APC HN)** - Bản đặc tả kiến trúc 80 bảng, 5 Domain cốt lõi.
Tài liệu gốc: `sources/sach-ky-nang/chien-luoc-kien-truc-doanh-nghiep.md` & `sources/sach-ky-nang/system-architecture-blueprint-lms-viet-my.md`.

---

## 3. Các mô hình & khung quản trị thực chiến

### 3.1. Ma trận 4 Mô hình Hoạt động (Operating Model Matrix)
Xác định mô hình vận hành của tổ chức dựa trên 2 trục:
1. **Mức độ chuẩn hóa quy trình (Process Standardization):** Quy trình giữa các cơ sở/phòng ban có giống hệt nhau không?
2. **Mức độ tích hợp dữ liệu (Data Integration):** Dữ liệu học viên, tài chính, giảng viên có liên thông thời gian thực không?

| Mô hình | Chuẩn hóa quy trình | Tích hợp dữ liệu | Đặc thù & Ứng dụng thực tế |
| :--- | :--- | :--- | :--- |
| **Phối hợp (Coordination)** | Thấp | Cao | Các cơ sở tự chủ giáo trình nhưng dùng chung hồ sơ sinh viên và cổng thanh toán tập trung. |
| **Hợp nhất (Unification)** | Cao | Cao | Chuẩn hóa tuyệt đối toàn hệ thống từ tuyển sinh, đào tạo đến khảo thí (mô hình tối ưu cho APC HN). |
| **Đa dạng hóa (Diversification)** | Thấp | Thấp | Tập đoàn đa ngành quản lý các đơn vị thành viên tự chủ hoàn toàn. |
| **Nhân bản (Replication)** | Cao | Thấp | Quy trình vận hành chuẩn hóa cao nhưng dữ liệu các chi nhánh tách biệt độc lập (chuỗi nhượng quyền). |

### 3.2. Lộ trình 4 giai đoạn trưởng thành kiến trúc (Architecture Maturity)
1. **Ứng dụng Silo (Business Silos):** Phòng ban tự phát triển phần mềm cục bộ; dữ liệu phân mảnh, báo cáo lệch nhau.
2. **Tiêu chuẩn hóa công nghệ (Standardized Technology):** Quy chuẩn hạ tầng server, chuẩn CSDL, an ninh mạng và cổng kết nối API.
3. **Tối ưu hóa lõi doanh nghiệp (Optimized Core):** Xây dựng CSDL dùng chung (Master Data), tự động hóa các quy trình lõi (tuyển sinh - học vụ - điểm danh - học phí).
4. **Module hóa kinh doanh (Business Modularity):** Hệ thống cắm rút linh hoạt qua API/MCP, cho phép mở rộng phân hiệu mới nhanh chóng.

### 3.3. Bộ tiêu chuẩn thẩm định hệ thống giáo dục (Thước đo Blueprint LMS 80 bảng)
Mọi giải pháp phần mềm trường học khi đưa vào đánh giá phải được đối soát qua 5 Domain cốt lõi:
- **Domain 1: Tổ chức & Nhân sự:** Ma trận phân quyền RBAC đa cấp (Trường -> Khoa -> Bộ môn -> Lớp), kiểm soát truy cập và bảo mật tenant.
- **Domain 2: Khung chương trình & Đào tạo:** Quản lý cây học phần, tiên quyết, tín chỉ/niên chế, chuẩn đầu ra BTEC và chính quy.
- **Domain 3: Kế hoạch & Học vụ:** Thời khóa biểu động, quản lý phòng máy/xưởng thực hành, tích hợp API điểm danh thời gian thực (CIS Production).
- **Domain 4: Quản lý Sinh viên & Khảo thí:** Hồ sơ 5.137 sinh viên (CMS API), ngân hàng đề thi, bảng điểm có lịch sử kiểm toán (audit trail) bất biến.
- **Domain 5: Tài chính & Học phí:** Quản lý hóa đơn điện tử, công nợ học phí, chính sách học bổng và đối soát tự động.

---

## 4. Checklist thẩm định hệ thống phần mềm
- [ ] Phần mềm có thỏa mãn mô hình hoạt động (Operating Model) đã định vị của trường không?
- [ ] Dữ liệu sinh viên và điểm số có được cô lập logic an toàn (Tenant Isolation) hay đang dùng chung bảng nguy hiểm?
- [ ] Hệ thống có cung cấp đầy đủ REST API để kết nối với các ứng dụng khác (như Javis OS / CIS / CMS) không?
- [ ] Cấu trúc dữ liệu có bao phủ đủ 5 Domain cốt lõi của trường học không?
- [ ] Nhà cung cấp có cam kết bàn giao toàn bộ dữ liệu sạch khi dừng hợp đồng không?
- [ ] Văn bản không sử dụng ký tự em dash?
