# mixie-buff-itch

**Tiếng Việt** | [English](README.en.md)

## Mô tả

`mixie-buff-itch` là công cụ Python có giao diện, dùng Playwright để truy cập một game itch.io qua nhiều profile trình duyệt độc lập. Tool tạo các phiên mở trang, thử mở/chạy game WebGL hoặc bắt đầu tải file rồi hủy, phục vụ học tập và thử nghiệm hành vi thường được gọi là **“buff view / download / play”**.

Nếu game đã tích hợp GameAnalytics, việc game thực sự khởi chạy có thể khiến SDK gửi sự kiện và phát sinh số liệu trong dự án analytics đó. Tool quan sát các request có chuỗi `gameanalytics` trong URL; tool không tự tích hợp SDK, không trực tiếp gửi sự kiện giả và không yêu cầu nhập API key GameAnalytics.

**Không cam kết mỗi profile được tính thành một view, download, lượt chơi hay người dùng mới.** Profile riêng tách cookie và dữ liệu lưu trữ, không tự thay đổi IP hoặc bảo đảm được nhận diện là người dùng khác. Kết quả thực tế cần được kiểm tra trong dashboard tương ứng. Nên dùng game và dự án GameAnalytics TEST mà bạn quản lý để tránh làm sai lệch số liệu thật.

## Chức năng và giới hạn

- Tạo **1–100 profile mới** mỗi lượt; giữ lại profile để chạy lại.
- Chọn Chromium do Playwright cài hoặc Brave đã có trên máy.
- Mở trang game, thử nhấn **Run game / Play game**, rồi giữ phiên theo thời lượng cấu hình. Auto Play không điều khiển nhân vật, hoàn thành màn chơi hay tự nhấn mọi nút bên trong game.
- Chế độ download nhấn **Download Now**, bỏ qua quyên góp tùy chọn nếu có, nhấn nút tải file đầu tiên đang hiển thị rồi hủy. Không thanh toán hoặc vượt qua trang bắt buộc mua game.
- Các profile chạy **lần lượt**, không đồng thời. Một lượt chọn chế độ game hoặc download; chế độ download không chạy game để tạo sự kiện gameplay.
- Giao diện Tiếng Việt / English, lưu cấu hình cục bộ và xuất CSV.

## Yêu cầu

- Windows 10/11 là môi trường hướng dẫn và các file BAT hỗ trợ.
- Python **3.10 trở lên**, có Tkinter và pip. Cần lệnh `py` hoạt động nếu chạy BAT.
- Internet để cài thư viện, tải trình duyệt và truy cập game.
- Brave cần cài riêng nếu bạn chọn nó. Chromium do Playwright tải là bản riêng, không phải Chrome/Brave cá nhân của bạn.

## Cài đặt và chạy

Clone repository hoặc tải ZIP rồi giải nén. Khi dùng lệnh bên dưới, mở terminal tại thư mục chứa `mixie_buff_itch.py`.

### Cách 1: Dùng file BAT

1. Cài Python theo yêu cầu ở trên.
2. Chạy **`INSTALL_MIXIE_BUFF_ITCH.bat`** một lần để cài thư viện và Chromium. Đợi dòng `Setup complete.`.
3. Chạy **`RUN_MIXIE_BUFF_ITCH.bat`** để mở tool.

File INSTALL cài bằng hai lệnh đầu; file RUN chuyển về thư mục dự án rồi gọi lệnh cuối:

```powershell
py -m pip install playwright
py -m playwright install chromium
py mixie_buff_itch.py
```

### Cách 2: Đọc mã nguồn và chạy Python trực tiếp

Nếu chưa yên tâm về file BAT, hãy mở chúng bằng trình soạn thảo, đọc `mixie_buff_itch.py`, rồi tự chạy:

```powershell
python --version
python -m pip install playwright
python -m playwright install chromium
python mixie_buff_itch.py
```

Hai cách dùng **cùng một mã nguồn**. Chạy trực tiếp giúp kiểm tra rõ các lệnh, không tự chứng minh mã nguồn hoặc thư viện là an toàn. Nếu có nhiều bản Python, dùng cùng một trình thông dịch để cài và chạy; có thể thay `python` bằng `py` nếu launcher này hoạt động.

## Cấu hình trong giao diện

| Trường / tùy chọn | Điền hoặc chọn gì |
| --- | --- |
| Ngôn ngữ / Language | Chọn **Tiếng Việt** hoặc **English** ở góc trên bên phải. Đổi ngay và lưu lựa chọn; log cũ và mã CSV giữ nguyên. |
| URL itch.io | URL trang game dùng HTTPS, ví dụ `https://your-studio.itch.io/your-game`. Thay URL game mẫu bằng game bạn được phép kiểm thử. Không điền link tải file trực tiếp hoặc dashboard analytics. |
| Trình duyệt | **Chromium** dùng bản do Playwright cài; **Brave** được tìm tại các vị trí cài đặt Windows phổ biến. |
| Số profile mới | Số nguyên **1–100**. Quyết định số profile tạo khi nhấn nút tạo mới; chạy lại dùng các profile được chọn trong danh sách. |
| Thời lượng mỗi phiên | Số nguyên **10–3600 giây** giữ phiên sau khi mở trang và thử Auto Play. Không áp dụng trong chế độ download. |
| Nghỉ giữa các phiên | Số nguyên **0–600 giây** giữa hai profile. |
| Tự nhấn Run game | Thử tìm và nhấn nút mở game. Bỏ chọn nếu chỉ muốn mở trang; game tự chạy trên trang vẫn có thể khởi động. Không áp dụng trong chế độ download. |
| Tắt âm thanh | Tắt đầu ra âm thanh trình duyệt; không đổi cài đặt âm thanh bên trong game. |
| Chạy ẩn / headless | Không hiện cửa sổ trình duyệt. Có thể gây lỗi WebGL; nên để tắt khi thử lần đầu để quan sát. |
| Download rồi hủy file | Bật để dùng luồng tải rồi hủy thay cho luồng game. Tắt để quay về mở/chạy game. |

Tool vẫn kiểm tra toàn bộ giới hạn số trên khi chạy lại profile hoặc dùng chế độ download. Giữ các ô này hợp lệ dù chúng không quyết định hành vi của chế độ đang chọn.

### Tạo profile mới

1. Điền URL và chọn chế độ muốn thử.
2. Nhập số profile, thời lượng và thời gian nghỉ hợp lệ.
3. Nhấn **Tạo & chạy profile mới / Create & run new profiles**.
4. Theo dõi trạng thái, tiến trình và nhật ký. Profile có tên `user_001`, `user_002`, …; lượt tạo sau tiếp tục từ số lớn nhất đã lưu.

### Chạy lại profile đã lưu

1. Nhấn **Làm mới / Refresh** nếu cần cập nhật danh sách.
2. Chọn một hoặc nhiều profile bằng Ctrl / Shift, hoặc **Chọn tất cả / Select all**.
3. Nhấn **Chạy profile đã chọn / Run selected profiles**. Cookie và dữ liệu cũ được giữ lại; đây không phải profile mới.

### Dừng và đóng

Nhấn **Dừng sau phiên hiện tại / Stop after current session**. Tool hoàn tất phiên đang chạy rồi dừng trước profile tiếp theo. Ứng dụng chặn thao tác đóng cửa sổ khi đang chạy. Không tắt cưỡng bức tiến trình hoặc mở cùng một profile trong nhiều phiên tool vì có thể gây lỗi hoặc hỏng dữ liệu profile.

### Lưu ý về download và GameAnalytics

- Tool bắt đầu tải rồi yêu cầu hủy ngay; file nhỏ có thể tải xong trước khi hủy.
- Có hỗ trợ trường hợp bỏ qua quyên góp mở trang tải ở tab mới. Thay đổi giao diện itch.io vẫn có thể khiến thao tác thất bại.
- Tải bị hủy không bảo đảm được itch.io tính lượt. Tải game không đồng nghĩa chạy game hay gửi sự kiện GameAnalytics.
- `ga_requests` chỉ đếm request quan sát được có chuỗi `gameanalytics` trong URL, không kiểm tra phản hồi thành công hay xác nhận hệ thống đã ghi nhận sự kiện. Đây không phải số event, session hay New User.
- Profile mới không bảo đảm tạo định danh analytics mới; còn phụ thuộc cách game/SDK tạo và lưu định danh. Chỉ game đã tích hợp analytics mới có thể phát sinh sự kiện của game khi chạy.

## Dữ liệu và báo cáo

Các đường dẫn nằm cạnh file Python, được tạo/lưu trong quá trình dùng:

| Đường dẫn | Nội dung |
| --- | --- |
| `mixie-buff-itch_profiles/` | Profile tái sử dụng; có thể chứa cookie, lịch sử và dữ liệu phiên. |
| `mixie-buff-itch_reports/` | Báo cáo CSV cho từng lượt chạy. Nút **Mở báo cáo / Open reports** mở thư mục này. |
| `mixie-buff-itch_settings.json` | URL, ngôn ngữ và lựa chọn gần nhất. Cấu hình qua giao diện; không cần tự tạo file. |

| Cột CSV | Ý nghĩa |
| --- | --- |
| `timestamp_utc`, `profile`, `profile_reused`, `browser` | Thời điểm UTC lúc bắt đầu phiên, tên profile, profile đã có dữ liệu hay chưa và trình duyệt. |
| `status` | `game_iframe_detected`: thấy iframe; `page_opened_no_iframe`: trang mở nhưng không thấy iframe; `download_cancelled`: đã hủy tải; `download_completed_before_cancel`: tải xong trước khi hủy; `error`: phiên gặp lỗi. Thấy iframe không chứng minh đã chơi game thành công. |
| `play_action`, `download_action` | Kết quả thao tác mở game hoặc tên file tải; có thể là `disabled`, `not_started`, `failed` tùy luồng. |
| `ga_requests`, `ga_hosts` | Số request khớp bộ lọc GameAnalytics và hostname tương ứng. |
| `iframe_count`, `page_errors` | Số iframe quan sát trong luồng game; lỗi trang và lỗi phiên thu thập được. |

Đọc CSV bằng trình soạn thảo hoặc ứng dụng bảng tính. Báo cáo chỉ thể hiện hoạt động trình duyệt mà tool quan sát được, không thay thế dashboard itch.io hay GameAnalytics.

## Xử lý lỗi thường gặp

| Hiện tượng | Cách kiểm tra |
| --- | --- |
| `py` không tìm thấy Python / `No installed Python found` | Thử `python --version` và cách chạy trực tiếp; kiểm tra cài đặt Python và launcher. |
| `No module named playwright` | Chạy `python -m pip install playwright` bằng đúng Python dùng mở tool. |
| Không tìm thấy executable Chromium | Chạy `python -m playwright install chromium` bằng cùng trình thông dịch. |
| Lỗi `tkinter`, `init.tcl`, Tk/Tcl | Kiểm tra/cài lại Python có Tcl/Tk và Tkinter. Thử `python -m tkinter` để kiểm tra cửa sổ Tk. |
| Không tìm thấy Brave | Cài Brave ở vị trí thông thường hoặc chọn Chromium. |
| Game không mở / WebGL lỗi | Tắt headless, kiểm tra URL và thử mở thủ công trong trình duyệt để xác định nút/điều kiện game yêu cầu. |
| Không thấy nút tải / timeout | Kiểm tra có file tải miễn phí, nút Download Now và luồng tải được hỗ trợ; xem `page_errors` trong CSV. |
| Windows báo publisher chưa xác minh | Đọc file và xác minh nguồn trước. Với ZIP tải về mà bạn tin tưởng, có thể chọn Properties → Unblock trước khi giải nén. |
| Có request analytics nhưng dashboard không tăng | Kiểm tra game/SDK, dự án analytics và dữ liệu trong dashboard; request được quan sát không phải xác nhận hệ thống đã tính lượt. |

## Mục đích sử dụng và trách nhiệm

**Dự án này sinh ra với mục đích học tập, không lạm dụng, tự chịu trách nhiệm khi dùng.**

Chỉ sử dụng với game/hệ thống bạn sở hữu hoặc được phép kiểm thử. Không dùng để gian lận thành tích, làm sai lệch số liệu thương mại hoặc gây tải không mong muốn. Người dùng chịu trách nhiệm về hành vi sử dụng, dữ liệu phát sinh và việc tuân thủ quy định của dịch vụ liên quan. Dự án không cam kết tăng chỉ số hay tránh được giới hạn/hạn chế tài khoản.
