int fib(int n) {
    int a, b, sum, i, j;
    if(n <= 1) {
        return 0;
    }
    else if(n == 2 || n == 3) {
        return 1;
    }

    i = n-1;
    j = n-2;
    a = fib(i);
    b = fib(j);
    sum = a+b;
    return sum;
}

int main() {
    int x, ans;
    input(x);
    ans = fib(x);
    output(ans);
    return 0;
}