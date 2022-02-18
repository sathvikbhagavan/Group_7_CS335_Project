struct Complex {
    float r;
    float i;
};

int main() {
    struct Complex c1 = {1.0, 2.0};
    struct Complex c2 = {2.0, 3.0};
    struct Complex c3;
    c3.r = c1.r + c2.r;
    c3.i = c1.i + c2.i;
}