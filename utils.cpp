#include "utils.h"

const string PROJECTPATH = "/abspath/to/process_man/";

Script::Script(string script_line){
    stringstream ss(script_line);
    ss >> id >> submit_time >> cwd;
    vector<string> tmp_script;
    string tmp;
    while(ss >> tmp){
        tmp_script.push_back(tmp);
    }
    status = tmp_script.back();
    tmp_script.pop_back();
    for(int i = 0; i < (int)tmp_script.size(); i++){
        script += tmp_script[i] + (i == (int)tmp_script.size() - 1 ? "" : " ");
    }
}

string format_output(Script script){
    stringstream ss;
    if(script.id == -1){
        ss << left << setw(3) << "id" << '\t'
        << left << setw(25) << "submit_time"
        << setw(60) << "cwd"
        << setw(60) << "script" << "\t" << "status";
    }else{
        ss << right << setw(3) << setfill('0') << script.id << '\t';
        ss << left << setw(25) << setfill(' ') << script.submit_time;
        ss << left << setw(60) << setfill(' ') << script.cwd;
        ss << left << setw(60) << script.script;
        ss << "\t" << script.status;
    }
    return ss.str();
}

ostream& operator<<(ostream &os, const Script &script){
    os << format_output(script);
    return os;
}
