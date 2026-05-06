import reflex as rx

from ..models.logger_state import LoggerState


def _badge_color(level: rx.Var) -> rx.Var:
    return rx.match(
        level,
        ("success", "green"),
        ("error", "red"),
        ("warning", "orange"),
        "gray",
    )


def _log_row(entry: dict) -> rx.Component:
    return rx.hstack(
        rx.text(
            entry["timestamp"],
            color="#9CA3AF",
            font_size="0.6rem",
            white_space="nowrap",
            min_width="48px",
            flex_shrink="0",
        ),
        rx.badge(
            entry["level"],
            color_scheme=_badge_color(entry["level"]),
            size="1",
            flex_shrink="0",
        ),
        rx.text(
            entry["message"],
            font_size="0.68rem",
            color="#374151",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
            flex="1",
            min_width="0",
        ),
        width="100%",
        spacing="1",
        align="center",
        padding_x="4px",
        padding_y="1px",
        border_bottom="1px solid #F3F4F6",
    )


def logger_panel() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(
                "Activity Log",
                font_weight="600",
                font_size="0.72rem",
                color="#374151",
            ),
            rx.spacer(),
            rx.badge(
                LoggerState.entries.length(),
                color_scheme="gray",
                size="1",
            ),
            rx.button(
                "Clear",
                on_click=LoggerState.clear,
                size="1",
                variant="ghost",
                color_scheme="gray",
                cursor="pointer",
            ),
            align="center",
            padding="6px 8px",
            border_bottom="1px solid #E5E7EB",
            flex_shrink="0",
        ),
        rx.box(
            rx.foreach(LoggerState.entries, _log_row),
            overflow_y="auto",
            height="100%",
            padding="2px 0",
        ),
        display="flex",
        flex_direction="column",
        height="100%",
        border_right="1px solid #E5E7EB",
        bg="#FAFAFA",
        font_family="'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        overflow="hidden",
    )
