#include "utils.h"

int main(){

    ifstream file(QUEUEPATH);
    string line;
    cout << format_output() << endl;
    if(file.is_open()){
        int line_num = 0;
        while(getline(file, line)){
            Script script(line);
            cout << script << endl;
            line_num ++;
        }
        file.close();
        cout << "Total process: " << line_num << endl;
    }else{
        cout << "Failed to open file." << endl;
    }

    return 0;
}