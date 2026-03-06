import tempfile
import unittest
from pathlib import Path

from publish_to_wechat import build_digest, build_wechat_html, read_article_file


class WeChatPublisherHelpersTest(unittest.TestCase):
    def test_read_article_file_uses_first_non_empty_line_as_title(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            article_path = Path(temp_dir) / "article.txt"
            article_path.write_text(
                "\n公众号标题\n\n第一段内容\n\n一、第二部分\n\n更多内容\n",
                encoding="utf-8",
            )

            article = read_article_file(str(article_path))

            self.assertEqual(article.title, "公众号标题")
            self.assertIn("第一段内容", article.body_text)
            self.assertIn("一、第二部分", article.body_text)

    def test_build_wechat_html_promotes_section_headings(self):
        body_text = "导语内容\n\n一、核心部分\n\n1. 小节\n\n说明："

        html_output = build_wechat_html(body_text)

        self.assertIn("<h2", html_output)
        self.assertIn("一、核心部分", html_output)
        self.assertIn("font-weight:700", html_output)

    def test_build_digest_trims_long_text(self):
        digest = build_digest("这是一段测试内容 " * 20, max_length=30)
        self.assertLessEqual(len(digest), 30)


if __name__ == "__main__":
    unittest.main()
