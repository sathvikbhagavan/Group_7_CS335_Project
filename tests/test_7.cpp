struct Complex{
    float real;
    float imag;
};

int main() {
    struct Complex A;
    struct Complex B;
    int r, i;
    A.real = 1;
    A.imag = 0;
    B.real = 20;
    B.imag = 0;
    r = A.real + B.real;
    i = A.imag + B.imag;
    output(r);
    output(" + i ");
    output(i);
    return 0;
}