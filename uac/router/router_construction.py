from typing import Optional

from pydantic import BaseModel, Field


class QuestionAnswering(BaseModel):
    """Sử dụng QuestionAnswering khi được yêu cầu cung cấp những thông tin chung về trường, chương trình đào tạo, ngành học, thông tin tuyển sinh của trường Đại học Đông Á.
    - Thông tin về trường Đại học Đông Á: Thông tin về mã trường, Địa chỉ, Điện thoại hotline, Website, fanpage, Chính sách học bổng
    - Chương trình đào tạo, ngành học: Các ngành đào tạo, Thông tin về học phí, Số lượng tín chỉ, Số năm học của ngành học
    - Thông tin về tuyển sinh: Đối tượng tuyển sinh, Phạm vi tuyển sinh, Phương thức tuyển sinh, Thông tin về tên ngành, mã ngành, tổ hợp xét tuyển, mã tổ hợp xét tuyển, Thời gian xét tuyển, Hồ sơ, giấy tờ xét tuyển, Chỉ tiêu xét tuyển , Địa điểm và cách thức hồ sơ xét tuyển, Cơ hội nghề nghiệp sau khi tốt nghiệp
    """

    topic: Optional[str] = Field(
        description="Những thông tin mà sinh viên cần tư vấn về trường, chương trình đào tạo, ngành học, thông tin tuyển sinh của trường Đại học Đông Á."
    )

class OutOfDomian(BaseModel):
    """Sử dụng OutOfDomian khi bạn nhận được những yêu cầu nằm ngoài phạm vi thông tin tuyển sinh của trường Đại học Đông Á.
    - Các yêu cầu có thể là những câu hỏi thông thường như chào hỏi và các yêu cầu về những lĩnh vực khác không phải về tuyển sinh
    Ví dụ:
    - Xin chào
    - Thời tiết hôm nay là gì?
    """

    question_type : Optional[str] = Field(
        description="Yêu cầu nằm ngoại phạm vi tuyển sinh của Trường Đại học Đông Á"
    )