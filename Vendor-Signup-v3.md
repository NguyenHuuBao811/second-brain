# Vendor Signup

### Quy tắc validate mặc định cho Input

Đối với các trường dạng Text Input không có yêu cầu validate riêng:

- **Độ dài tối đa:** 255 ký tự
- **Khoảng trắng:** Tự động loại bỏ khoảng trắng ở đầu và cuối chuỗi
- **Giá trị rỗng:**
    - Trường bắt buộc không được để trống hoặc chỉ nhập khoảng trắng
    - Trường không bắt buộc được phép để trống
- **Ký tự:** Không giới hạn ký tự đặc biệt nếu nghiệp vụ không quy định format riêng
- **Định dạng:** Không yêu cầu kiểm tra định dạng đặc biệt
- Nếu trường có quy tắc nghiệp vụ riêng, áp dụng rule riêng của trường đó thay cho rule mặc định

### Vendor đăng ký tài khoản (trên Vendor App)

#### UC Description

|**Description**|- Màn hình **Vendor Signup** trên **Vendor App** cho phép Vendor tự đăng ký tài khoản trực tiếp trên Vendor App.<br>- Sau khi Submit, Vendor App gửi đơn đăng ký sang **FF V3** để Admin FF phê duyệt.<br>- Quá trình đăng ký gồm 2 bước: **Bước 1 – Thông tin chung** và **Bước 2 – Năng lực sản xuất** (Technique, Shipping mode, First warehouse, Cấu hình sản xuất).<br>- Thông tin đăng ký phải khớp với form **Create Vendor** của role Admin.<br>- Form Signup **không** có trường mật khẩu. Khi Admin FF phê duyệt trên FF V3, FF trả kết quả về **Vendor App** để tự động tạo Vendor và tài khoản **Owner** cho email đăng ký, sau đó gửi thông tin đăng nhập qua email.|
|---|---|
|**Actor**|Vendor (Guest – chưa có tài khoản)|
|**Trigger**|Vendor truy cập trang đăng nhập **Vendor App** và chọn **Sign up**|
|**Pre-conditions**|- Kết nối giữa Vendor App và FF V3 hoạt động bình thường.<br>- Danh sách Technique trên FF V3 đã được cấu hình và có ít nhất 01 Technique ở trạng thái Active.<br>- Danh sách Country, Timezone đã được cấu hình.<br>- [TBD] Danh sách Warehouse đã được cấu hình.<br>- Email đăng ký chưa thuộc tài khoản Vendor nào đang tồn tại hoặc đang chờ duyệt.|
|**Post-conditions**|Nếu Submit thành công<br>- Vendor App gửi đơn đăng ký sang FF V3 thành công<br>- Trên FF V3: đơn đăng ký Vendor được tạo với trạng thái **Waiting for approval**, xuất hiện trong Vendor List của Admin FF<br>- Hiển thị thông báo đăng ký thành công, chờ Admin duyệt<br>- Gửi email xác nhận đã nhận đơn đăng ký (Email 1)<br>- **Chưa tạo tài khoản đăng nhập**, Vendor chưa thể đăng nhập cho đến khi được phê duyệt<br>Nếu Submit thất bại<br>- Không tạo dữ liệu<br>- Toàn bộ dữ liệu người dùng vẫn được giữ nguyên trên màn hình<br>- Báo lỗi|
|**Main Flow**|1. Vendor mở màn hình Signup trên Vendor App, hệ thống hiển thị **Bước 1 – Thông tin chung**<br>2. Vendor nhập thông tin chung (bao gồm Tên pháp lý, Mã quốc gia, Múi giờ, Email,...) và chọn **Next**<br>3. Hệ thống validate Bước 1<br>    - Nếu hợp lệ → chuyển sang Bước 2<br>4. Vendor chọn Technique, Shipping mode, First warehouse, Cấu hình sản xuất<br>5. Vendor chọn **Submit**<br>6. Vendor App validate toàn bộ form, bao gồm check trùng **Email** và **Code** trên dữ liệu Vendor App<br>7. Vendor App lưu đơn đăng ký (trạng thái **Waiting for approval**) và gửi sang FF V3<br>8. FF V3 tạo đơn đăng ký với trạng thái **Waiting for approval** và trả kết quả về Vendor App<br>9. Vendor App hiển thị thông báo đăng ký thành công, chờ phê duyệt|
|**Alternative Flow**|- Vendor chọn **Back** ở Bước 2 → Quay về Bước 1, giữ nguyên dữ liệu đã nhập ở cả 2 bước<br>- Vendor dùng **Email** và/hoặc **Code** của một đơn đăng ký đã bị Reject → Cho phép đăng ký lại (không check trùng với đơn đã Reject)|
|**Exception Flow**|- Submit khi thiếu Required Field<br>→ Không lưu<br>→ Scroll tới field đầu tiên bị lỗi<br>- Email đã tồn tại (Vendor đang Active/Waiting for approval) → Không tạo đơn đăng ký<br>- Code đã tồn tại (Vendor hoặc đơn đang chờ duyệt trên Vendor App) → Không tạo đơn đăng ký<br>- Không kết nối được FF V3 / timeout → Không tạo đơn đăng ký (kể cả trên Vendor App), hiển thị thông báo lỗi, giữ nguyên dữ liệu<br>- Lỗi hệ thống khi Submit → Không tạo dữ liệu, hiển thị thông báo lỗi, giữ nguyên dữ liệu|
|**Validate Rules**|Xem mục **Validation Rules** bên dưới|
|**Business Rule**|- Master data trên form (Technique, Country, Timezone, Warehouse,...) được Vendor App lấy từ FF V3<br>- Thông tin Vendor và tài khoản được lưu trên **Vendor App** → Check trùng Email, Code thực hiện **ngay trên Vendor App**, không gọi sang FF V3<br>- Bước 1 – Thông tin chung:<br>    - Các trường phải khớp với form **Create Vendor** của Admin [TBD: bổ sung danh sách đầy đủ theo ảnh thiết kế]<br>    - Bổ sung các trường: **Tên pháp lý**, **Mã quốc gia**, **Múi giờ**<br>    - Email check trùng trên Vendor App với tài khoản user đang tồn tại và đơn đăng ký đang Waiting for approval; **không check trùng với các đơn đăng ký đã bị Reject**<br>    - **Code** check trùng trên Vendor App với Vendor đang tồn tại và đơn đăng ký đang Waiting for approval; **không check trùng với các đơn đăng ký đã bị Reject**<br>- Bước 2 – Năng lực sản xuất:<br>    - **Technique:** Danh sách lấy theo các Technique đang **Active** ở menu Techniques, cho phép chọn nhiều [TBD: xác nhận multi-select]<br>    - **Shipping mode:** Chọn 1 trong 3 giá trị: **Tự ship**, **Processed by Printway**, **Hybrid**<br>    - **First warehouse:** [TBD: nguồn dữ liệu và các trường thông tin]<br>    - **Cấu hình sản xuất:** Chọn 1 trong 3 giá trị (giống mục Cấu hình sản xuất ở màn Vendor detail), default = **Sản xuất theo mã đơn**:<br>        - **Sản xuất theo mã đơn:** Luồng mặc định, xưởng quét mã đơn ở 3 trạm Assize / Label / Shipping<br>        - **Sản xuất theo Sub-barcode:** Cấu hình workflow theo product group và các trạm scan sản xuất<br>        - **Vendor dùng hệ thống riêng:** Nhân sự PW (role Staff) xử lý đơn của vendor ở 3 trạm Assize / Label / Shipping<br>- Trạng thái sau đăng ký: **Waiting for approval**. Ở trạng thái này (và **Rejected**) chưa có tài khoản đăng nhập → Vendor không thể đăng nhập<br>- Tài khoản đăng nhập chỉ được tạo khi Admin **Approve** (xem UC Phê duyệt đăng ký Vendor)<br>- Thay đổi liên quan ở form **Create Vendor** (role Admin): sửa list option **Shipping mode** gồm 3 lựa chọn: Tự ship, Processed by Printway, Hybrid|

#### Validation Rules

|**Field**|**Validation Rule**|**Error Message (VI)**|**Error Message (EN)**|
|---|---|---|---|
|Button Next / Submit|Không cho thao tác khi còn Required Field chưa nhập → Disable|||
|Tên pháp lý|Required|Vui lòng nhập tên pháp lý.|Please enter the legal name.|
|Mã quốc gia|Required|Vui lòng chọn mã quốc gia.|Please select a country code.|
|Múi giờ|Required|Vui lòng chọn múi giờ.|Please select a timezone.|
|Email|Required|Vui lòng nhập email.|Please enter your email.|
|Email|Đúng định dạng email|Email không hợp lệ.|Invalid email address.|
|Email|Unique trên Vendor App: user + đơn đang chờ duyệt (trừ đơn đã Reject)|Email đã được sử dụng.|This email is already in use.|
|Code|Unique trên Vendor App: Vendor + đơn đang chờ duyệt (trừ đơn đã Reject)|Mã Vendor đã tồn tại.|Vendor code already exists.|
|Technique|Required, chọn ít nhất 1|Vui lòng chọn ít nhất một Technique.|Please select at least one technique.|
|Technique|Phải ở trạng thái Active|Technique không còn khả dụng.|The selected technique is no longer available.|
|Shipping mode|Required|Vui lòng chọn Shipping mode.|Please select a shipping mode.|
|First warehouse|[TBD]|||
|Cấu hình sản xuất|Required, chọn 1 giá trị|Vui lòng chọn cấu hình sản xuất.|Please select a production configuration.|
|Button Submit|Không kết nối được FF V3 / timeout|Không thể gửi đơn đăng ký. Vui lòng thử lại.|Unable to submit your application. Please try again.|

### Phê duyệt đăng ký Vendor (trên FF V3)

#### UC Description

|**Description**|- Việc phê duyệt **chỉ thực hiện trên hệ thống Fulfillment (FF V3)**. Vendor App không có chức năng phê duyệt, chỉ nhận kết quả từ FF.<br>- Admin FF xem đơn đăng ký Vendor và thực hiện **Approve** hoặc **Reject**.<br>- Khi Approve: FF kích hoạt Vendor (Supplier) và gửi kết quả sang Vendor App để tạo Vendor + tài khoản Owner (xem UC **Vendor App nhận kết quả phê duyệt**).<br>- Khi Reject: FF gửi kết quả Reject về Vendor App để cập nhật trạng thái đơn, và gửi email thông báo từ chối kèm lý do.|
|---|---|
|**Actor**|Admin FF|
|**Trigger**|Admin chọn **Vendor → Vendor List** trên FF V3 và nhấn vào Vendor có trạng thái **Waiting for approval**|
|**Pre-conditions**|- Admin đăng nhập FF V3 thành công.<br>- Admin có quyền phê duyệt Vendor.<br>- Tồn tại đơn đăng ký có trạng thái **Waiting for approval**.|
|**Post-conditions**|Nếu Approve thành công<br>- Vendor trên FF V3 chuyển sang trạng thái **Active**<br>- Vendor App đã tạo Vendor và tài khoản Owner thành công<br>- Email thông tin đăng nhập được gửi cho Vendor (Email 2)<br>Nếu Reject thành công<br>- Vendor chuyển sang trạng thái **Rejected** trên cả FF V3 và Vendor App<br>- Không tạo Vendor / tài khoản trên Vendor App<br>- Gửi email thông báo từ chối kèm lý do (Email 3)<br>Nếu thất bại<br>- Không thay đổi trạng thái trên FF V3, không tạo dữ liệu trên Vendor App<br>- Báo lỗi trên FF V3|
|**Main Flow**|1. Admin mở Vendor List trên FF V3, hệ thống hiển thị danh sách Vendor kèm trạng thái<br>2. Admin nhấn vào Vendor có trạng thái **Waiting for approval**<br>3. Hệ thống hiển thị chi tiết thông tin đăng ký (Bước 1 và Bước 2)<br>4. Admin chọn **Approve**<br>5. FF gửi kết quả phê duyệt kèm thông tin Vendor sang Vendor App<br>6. Vendor App tạo Vendor + tài khoản Owner và trả kết quả về FF<br>7. Nếu Vendor App trả về thành công:<br>    - FF chuyển trạng thái Vendor sang **Active**<br>    - FF gửi email thông tin đăng nhập cho Vendor (Email 2)<br>    - Hiển thị thông báo phê duyệt thành công|
|**Alternative Flow**|- Admin chọn **Reject**<br>→ Hiển thị popup nhập **Lý do từ chối**<br>→ Admin nhập lý do và xác nhận<br>→ Vendor chuyển trạng thái **Rejected**, gửi email kèm lý do cho Vendor (Email 3)<br>- Admin đóng popup Reject → Không thay đổi trạng thái|
|**Exception Flow**|- Reject khi chưa nhập lý do → Không cho xác nhận<br>- Đơn đăng ký đã được Admin khác xử lý → Không cho thao tác, hiển thị thông báo và reload trạng thái mới nhất<br>- Vendor App trả về lỗi tạo dữ liệu → FF không Approve, giữ trạng thái **Waiting for approval**, hiển thị lỗi tương ứng trên FF V3<br>- Không kết nối được Vendor App / timeout → FF không Approve, giữ trạng thái **Waiting for approval**, báo lỗi<br>- Gửi email thất bại → Vẫn giữ kết quả Approve/Reject, hệ thống ghi log lỗi. **Không** có chức năng gửi lại email|
|**Validate Rules**|Xem mục **Validation Rules** bên dưới|
|**Business Rule**|- Chỉ đơn ở trạng thái **Waiting for approval** mới hiển thị button **Approve / Reject**<br>- Lý do từ chối bắt buộc nhập khi Reject<br>- FF V3 chỉ chuyển Vendor sang **Active** khi Vendor App xác nhận tạo dữ liệu thành công (đảm bảo dữ liệu 2 hệ thống đồng bộ)<br>- Toàn bộ email do hệ thống FF gửi, ngôn ngữ mặc định **tiếng Anh**<br>- Đơn đã Reject không được tính khi check trùng Email và Code, Vendor có thể đăng ký lại bằng Email/Code cũ<br>- Kết quả Reject bắt buộc được gửi về Vendor App để cập nhật trạng thái đơn → giải phóng Email/Code|

#### Validation Rules

|**Field**|**Validation Rule**|**Error Message (VI)**|**Error Message (EN)**|
|---|---|---|---|
|Lý do từ chối|Required|Vui lòng nhập lý do từ chối.|Please enter the rejection reason.|
|Lý do từ chối|Tối đa [TBD] ký tự|Lý do từ chối vượt quá số ký tự cho phép.|The rejection reason exceeds the maximum length.|
|Button Confirm Reject|Disable khi chưa nhập lý do từ chối|||
|Button Approve|Vendor App trả về lỗi khác / timeout|Không thể phê duyệt Vendor. Vui lòng thử lại.|Unable to approve the vendor. Please try again.|

### Vendor App nhận kết quả phê duyệt

#### UC Description

|**Description**|- Vendor App nhận kết quả **Approve** từ hệ thống FF V3 và tự động tạo Vendor + tài khoản Owner.<br>- Vendor App **không** có thao tác phê duyệt.<br>- Khi Admin FF Reject, FF cũng gửi kết quả về để Vendor App chuyển đơn sang **Rejected** (giải phóng Email/Code để đăng ký lại).|
|---|---|
|**Actor**|Hệ thống (FF V3 → Vendor App)|
|**Trigger**|Admin FF Approve đơn đăng ký Vendor (được gửi từ Vendor App) trên FF V3|
|**Pre-conditions**|- Kết nối giữa FF V3 và Vendor App hoạt động bình thường.<br>- FF gửi đầy đủ thông tin Vendor theo mapping ở mục Business Rule.|
|**Post-conditions**|Nếu xử lý thành công<br>- Vendor mới được tạo với trạng thái **active**, xuất hiện trong **Quản trị → Vendors** (tăng số Total vendors / Active)<br>- Tài khoản email đăng ký được tạo và gán role **Owner**, hiển thị ở tab **Users** của Vendor<br>- Trả kết quả thành công về FF<br>Nếu xử lý thất bại<br>- Không tạo dữ liệu (rollback toàn bộ)<br>- Trả mã lỗi về FF|
|**Main Flow**|1. Vendor App nhận kết quả Approve từ FF, xác định đơn đăng ký tương ứng đã lưu trên Vendor App<br>2. Chuyển đơn đăng ký sang trạng thái **Approved**<br>3. Tạo Vendor theo mapping<br>4. Tạo user với email đăng ký, sinh mật khẩu ngẫu nhiên, gán role **Owner**<br>5. Trả kết quả thành công kèm thông tin đăng nhập về FF để FF gửi email|
|**Alternative Flow**||
|**Exception Flow**|- Lỗi khi tạo Vendor hoặc user → Rollback toàn bộ, giữ đơn ở trạng thái **Waiting for approval**, trả lỗi về FF|
|**Validate Rules**|Email, Code đã được check trùng tại bước đăng ký (đơn Waiting for approval giữ chỗ Email/Code), không cần check lại|
|**Business Rule**|- Mapping dữ liệu khi tạo Vendor:<br>    - **Name** = **Tên hiển thị** Vendor đăng ký<br>    - **Code** = Code Vendor trên FF V3<br>    - **Status** = active<br>    - **FF Supplier link** = Vendor (Supplier) vừa được duyệt trên FF V3, gồm Supplier, Supplier code, FF id, Linked at = thời điểm Approve. Liên kết ở trạng thái **Locked**, muốn đổi Supplier phải xoá và tạo lại Vendor<br>    - **Cấu hình sản xuất** = giá trị Vendor chọn ở Bước 2 khi đăng ký<br>    - **API access** = Tắt (default)<br>- Tài khoản Owner:<br>    - **Username:** Email Vendor đã đăng ký<br>    - **Password:** Hệ thống tự sinh, tuân theo quy tắc mật khẩu hiện có của hệ thống<br>    - **Role:** Owner. Sau khi có Owner, có thể thêm user với role khác vào Vendor tại tab **Users**|

### Mẫu Email

- Ngôn ngữ mặc định: **tiếng Anh**
- Biến động đặt trong `{{ }}`
- Gửi thất bại: ghi log, không gửi lại

#### Email 1 – Application received

|**Trigger**|Vendor Submit đơn đăng ký thành công|
|---|---|
|**To**|`{{vendor_email}}`|
|**Subject**|[Printway] We've received your vendor application|
|**Body**|Hi `{{display_name}}`,<br><br>Thank you for applying to become a Printway Fulfillment vendor.<br>We have received your application with the following details:<br>- Display name: `{{display_name}}`<br>- Vendor code: `{{vendor_code}}`<br>- Email: `{{vendor_email}}`<br><br>Your application is now under review. We will notify you by email as soon as a decision has been made.<br><br>Best regards,<br>Printway Fulfillment Team|

#### Email 2 – Application approved & login credentials

|**Trigger**|Admin FF Approve đơn đăng ký thành công (Vendor App đã tạo tài khoản)|
|---|---|
|**To**|`{{vendor_email}}`|
|**Subject**|[Printway] Your vendor account has been approved|
|**Body**|Hi `{{display_name}}`,<br><br>Congratulations! Your vendor application has been approved.<br>You can now sign in to Vendor App with the following credentials:<br>- Login URL: `{{login_url}}`<br>- Username: `{{vendor_email}}`<br>- Password: `{{password}}`<br>- Role: Owner of vendor `{{display_name}}` (`{{vendor_code}}`)<br><br>For security reasons, we recommend changing your password after your first login and not sharing this email with anyone.<br><br>As the Owner, you can invite team members to your vendor from the **Users** tab.<br><br>If you need help, please contact `{{support_email}}`.<br><br>Best regards,<br>Printway Fulfillment Team|

#### Email 3 – Application rejected

|**Trigger**|Admin FF Reject đơn đăng ký|
|---|---|
|**To**|`{{vendor_email}}`|
|**Subject**|[Printway] Update on your vendor application|
|**Body**|Hi `{{display_name}}`,<br><br>Thank you for your interest in becoming a Printway Fulfillment vendor.<br>Unfortunately, your application was not approved for the following reason:<br><br>`{{reject_reason}}`<br><br>You are welcome to update your information and reapply with the same email at: `{{signup_url}}`<br><br>If you need help, please contact `{{support_email}}`.<br><br>Best regards,<br>Printway Fulfillment Team|
