#include <iostream>

int fun(int a, int b , float c=1.43e-1){
    if(a==1){
        output("$it is a valid program$");
    }
    return a<b?a:int(c)-1;
}

int main() {
    fun(1,2,3.45);
}