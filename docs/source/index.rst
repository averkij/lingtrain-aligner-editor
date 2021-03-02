.. Lingtrain Aligner documentation master file, created by
   sphinx-quickstart on Sun Feb 28 11:50:56 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Lingtrain Aligner documentation
=============================================

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

Lingtrain Aligner — это веб-приложение, которое поможет вам выровнять два текста на разных языках.
Сейчас поддерживается :ref:`10+ языков <languages>`, для любой пары из которых доступно выравнивание.

Первоначальная обработка происходит автоматически при помощи :ref:`предобученных моделей машинного обучения <technical>`.
Затем пользователь валидирует результат и дорабатывает полученный параллельный корпус до приемлемого качества.

Результат работы доступен для скачивания в txt и tmx форматах.



.. toctree::
   :maxdepth: 2
   :caption: Введение

   ui
   languages

.. toctree::
   :maxdepth: 2
   :caption: Быстрый старт

   preparing
   upload
   create-alignment

.. toctree::
   :maxdepth: 2
   :caption: Технические детали

   technical
