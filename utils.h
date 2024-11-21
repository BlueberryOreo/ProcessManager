#include <iostream>
#include <fstream>
#include <unistd.h>
#include <limits.h>
#include <vector>
#include <set>
#include <iomanip>
#include <ctime>
#include <sstream>
using namespace std;

#ifndef UTILS_H
#define UTILS_H
extern const char *QUEUEPATH;

struct Script{
    int id;
    string submit_time;
    string cwd;
    string script;
    string status;

    Script(int id=-1, string submit_time="", string cwd="", string script="", string status="") : id(id), submit_time(submit_time), cwd(cwd), script(script), status(status) {}
    Script(string script_line);
};

string format_output(Script script=Script());

ostream& operator<<(ostream &os, const Script &script);

#endif // UTILS_H