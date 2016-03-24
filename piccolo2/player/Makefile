PYUIC = pyuic4
SOURCES = player.ui connect.ui schedulelist.ui schedule.ui

all:	$(patsubst %.ui, %.py, $(SOURCES))

%.py:	%.ui
	$(PYUIC) $< -o $@
