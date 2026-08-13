#include<iostream>
using namespace std;
class demo { 
public: 
// <-- Added public access modifier
static void print(const string& m); // <-- Changed pointer (*) to reference (&) 
}; 
void demo::print(const string& m) { // <-- Matched the reference (&) here 
cout << m;
}
int main() {
demo::print("This is a string.");
return 0;
}