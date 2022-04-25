int factorial(int a){
    int k,t;
    if(a==1){
        return 1;
    }
    t = a-1;
    k = factorial(t);
    return a*k;
}


int main() {
    int x=7;
    int ans;
    ans = factorial(x);
    output(ans);
    return 0;
}