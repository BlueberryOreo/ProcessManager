CXX = g++
CXXFLAGS = -Wall -g -std=c++11

# 可执行文件的目标
TARGET = submit lsqueue rmqueue

# 源文件列表
SRCS = submit.cpp lsqueue.cpp rmqueue.cpp utils.cpp

# 生成的对象文件列表
OBJS = $(SRCS:.cpp=.o)

# 头文件
DEPS = utils.h

# 默认目标
all: $(TARGET)

# 每个目标的规则
submit: submit.o utils.o
	$(CXX) $(CXXFLAGS) submit.o utils.o -o $@

lsqueue: lsqueue.o utils.o
	$(CXX) $(CXXFLAGS) lsqueue.o utils.o -o $@

rmqueue: rmqueue.o utils.o
	$(CXX) $(CXXFLAGS) rmqueue.o utils.o -o $@

# 规则生成 .o 文件
%.o: %.cpp $(DEPS)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# 清理中间文件的规则
clean_objects:
	rm -f $(OBJS)

# 清理所有生成文件
clean:
	rm -f $(OBJS) $(TARGET)

# 伪目标
.PHONY: all clean clean_objects
