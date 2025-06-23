from PyQt6.QtCore import (
    QPropertyAnimation, QParallelAnimationGroup,
    QSequentialAnimationGroup, QEasingCurve, Qt
)
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt6.QtGui import QColor
from typing import Union, Optional, List, Tuple


class Animations:
    """Коллекция готовых анимаций для UI элементов"""

    @staticmethod
    def fade_in(widget: QWidget,
                duration: int = 300,
                easing: QEasingCurve.Type = QEasingCurve.Type.OutQuad,
                on_finished: Optional[callable] = None) -> QPropertyAnimation:
        """Плавное появление виджета"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setEasingCurve(easing)

        if on_finished:
            anim.finished.connect(on_finished)

        anim.start()
        return anim

    @staticmethod
    def fade_out(widget: QWidget,
                 duration: int = 300,
                 easing: QEasingCurve.Type = QEasingCurve.Type.InQuad,
                 on_finished: Optional[callable] = None) -> QPropertyAnimation:
        """Плавное исчезновение виджета"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.setEasingCurve(easing)

        if on_finished:
            anim.finished.connect(lambda: (on_finished(), widget.hide()))
        else:
            anim.finished.connect(widget.hide)

        anim.start()
        return anim

    @staticmethod
    def slide_in(widget: QWidget,
                 direction: Qt.Edge = Qt.Edge.LeftEdge,
                 distance: int = 100,
                 duration: int = 400,
                 easing: QEasingCurve.Type = QEasingCurve.Type.OutBack,
                 on_finished: Optional[callable] = None) -> QPropertyAnimation:
        """Анимация выезжания виджета с заданной стороны"""
        start_pos = widget.pos()

        if direction == Qt.Edge.LeftEdge:
            widget.move(start_pos.x() - distance, start_pos.y())
        elif direction == Qt.Edge.RightEdge:
            widget.move(start_pos.x() + distance, start_pos.y())
        elif direction == Qt.Edge.TopEdge:
            widget.move(start_pos.x(), start_pos.y() - distance)
        elif direction == Qt.Edge.BottomEdge:
            widget.move(start_pos.x(), start_pos.y() + distance)

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(widget.pos())
        anim.setEndValue(start_pos)
        anim.setEasingCurve(easing)

        if on_finished:
            anim.finished.connect(on_finished)

        anim.start()
        return anim

    @staticmethod
    def slide_out(widget: QWidget,
                  direction: Qt.Edge = Qt.Edge.RightEdge,
                  distance: int = 100,
                  duration: int = 400,
                  easing: QEasingCurve.Type = QEasingCurve.Type.InBack,
                  on_finished: Optional[callable] = None) -> QPropertyAnimation:
        """Анимация выезжания виджета за пределы экрана"""
        end_pos = widget.pos()

        if direction == Qt.Edge.LeftEdge:
            end_pos.setX(end_pos.x() - distance)
        elif direction == Qt.Edge.RightEdge:
            end_pos.setX(end_pos.x() + distance)
        elif direction == Qt.Edge.TopEdge:
            end_pos.setY(end_pos.y() - distance)
        elif direction == Qt.Edge.BottomEdge:
            end_pos.setY(end_pos.y() + distance)

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(widget.pos())
        anim.setEndValue(end_pos)
        anim.setEasingCurve(easing)

        if on_finished:
            anim.finished.connect(lambda: (on_finished(), widget.hide()))
        else:
            anim.finished.connect(widget.hide)

        anim.start()
        return anim

    @staticmethod
    def color_change(widget: QWidget,
                     start_color: Union[str, QColor],
                     end_color: Union[str, QColor],
                     duration: int = 500,
                     easing: QEasingCurve.Type = QEasingCurve.Type.InOutQuad,
                     property_name: bytes = b"background-color",
                     on_finished: Optional[callable] = None) -> QPropertyAnimation:
        """Анимация изменения цвета виджета"""
        anim = QPropertyAnimation(widget, property_name)
        anim.setDuration(duration)
        anim.setStartValue(QColor(start_color))
        anim.setEndValue(QColor(end_color))
        anim.setEasingCurve(easing)

        if on_finished:
            anim.finished.connect(on_finished)

        anim.start()
        return anim

    @staticmethod
    def shake(widget: QWidget,
              intensity: int = 10,
              duration: int = 500,
              on_finished: Optional[callable] = None) -> QSequentialAnimationGroup:
        """Анимация тряски (для ошибок или предупреждений)"""
        original_pos = widget.pos()
        animations = []

        # Создаем несколько микро-движений
        for i in range(5):
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(duration // 10)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            if i % 2 == 0:
                anim.setEndValue(original_pos + QPoint(intensity, 0))
            else:
                anim.setEndValue(original_pos - QPoint(intensity, 0))

            animations.append(anim)

        # Возврат в исходное положение
        final_anim = QPropertyAnimation(widget, b"pos")
        final_anim.setDuration(duration // 5)
        final_anim.setEndValue(original_pos)

        group = QSequentialAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        group.addAnimation(final_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        return group

    @staticmethod
    def pulse(widget: QWidget,
              scale_factor: float = 1.1,
              duration: int = 800,
              loops: int = -1,  # Бесконечно
              on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Анимация пульсации (для привлечения внимания)"""
        scale_anim = QPropertyAnimation(widget, b"geometry")
        scale_anim.setDuration(duration // 2)
        scale_anim.setKeyValueAt(0, widget.geometry())
        scale_anim.setKeyValueAt(0.5, widget.geometry().scaled(scale_factor, scale_factor,
                                                               Qt.AspectRatioMode.KeepAspectRatio))
        scale_anim.setKeyValueAt(1, widget.geometry())
        scale_anim.setLoopCount(loops)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setKeyValueAt(0, 1.0)
        opacity_anim.setKeyValueAt(0.5, 0.7)
        opacity_anim.setKeyValueAt(1, 1.0)
        opacity_anim.setLoopCount(loops)

        group = QParallelAnimationGroup()
        group.addAnimation(scale_anim)
        group.addAnimation(opacity_anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        return group

    @staticmethod
    def sequential_animations(widget: QWidget,
                              animations: List[Tuple[str, dict]],
                              on_finished: Optional[callable] = None) -> QSequentialAnimationGroup:
        """Последовательное выполнение нескольких анимаций"""
        group = QSequentialAnimationGroup()

        for anim_type, params in animations:
            if anim_type == "fade_in":
                anim = Animations.fade_in(widget, **params)
            elif anim_type == "fade_out":
                anim = Animations.fade_out(widget, **params)
            elif anim_type == "slide_in":
                anim = Animations.slide_in(widget, **params)
            elif anim_type == "slide_out":
                anim = Animations.slide_out(widget, **params)
            elif anim_type == "color_change":
                anim = Animations.color_change(widget, **params)
            elif anim_type == "shake":
                anim = Animations.shake(widget, **params)
            elif anim_type == "pulse":
                anim = Animations.pulse(widget, **params)
            else:
                continue

            group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        return group

    @staticmethod
    def parallel_animations(widget: QWidget,
                            animations: List[Tuple[str, dict]],
                            on_finished: Optional[callable] = None) -> QParallelAnimationGroup:
        """Параллельное выполнение нескольких анимаций"""
        group = QParallelAnimationGroup()

        for anim_type, params in animations:
            if anim_type == "fade_in":
                anim = Animations.fade_in(widget, **params)
            elif anim_type == "fade_out":
                anim = Animations.fade_out(widget, **params)
            elif anim_type == "slide_in":
                anim = Animations.slide_in(widget, **params)
            elif anim_type == "slide_out":
                anim = Animations.slide_out(widget, **params)
            elif anim_type == "color_change":
                anim = Animations.color_change(widget, **params)
            elif anim_type == "shake":
                anim = Animations.shake(widget, **params)
            elif anim_type == "pulse":
                anim = Animations.pulse(widget, **params)
            else:
                continue

            group.addAnimation(anim)

        if on_finished:
            group.finished.connect(on_finished)

        group.start()
        return group