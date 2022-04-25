int sum(int a, int b, int c, int d, int e) {
    int x;
    x = a+b+c+d+e;
    return x;
}

int main(){
    int s=0;
    s = sum(1, 2, 3, 4, 'a');
    output(s);
    return 0;
}