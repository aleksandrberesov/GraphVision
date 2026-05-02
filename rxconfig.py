import reflex as rx

config = rx.Config(
    app_name="GraphVision",
    frontend_port=3030,
    db_url="sqlite:///reflex.db",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)