CXX = g++
CXXFLAGS = -Wall -g

TARGET = submit lsqueue rmqueue

all: $(TARGET)

submit: submit.cpp
	$(CXX) $(CXXFLAGS) -o submit submit.cpp

lsqueue: lsqueue.cpp
	$(CXX) $(CXXFLAGS) -o lsqueue lsqueue.cpp

rmqueue: rmqueue.cpp
	$(CXX) $(CXXFLAGS) -o rmqueue rmqueue.cpp

clean:
	rm -f $(TARGET) *.o
	