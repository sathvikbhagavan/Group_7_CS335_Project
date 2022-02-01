// this is a comment

/*
    This is a comment
*/

class A {
    private:
        struct B{
            int a;
        };
        int x;
    public:
        int set(int a1, int x1) {
            this->B.a = a1;
            this->x = x1;
        }
};

A::sample() {
    output("hello world");
}

int main() {
    A a;
    int x1, a1;
    input(x1);
    input(a1);
    a.set(a1, x1);
    return 0;
}