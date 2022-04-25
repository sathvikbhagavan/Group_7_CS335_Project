int sum(int x, int y) {
    int ans;
    ans = x+y;
    return ans;
}

int main() {
    int a=1;
    a = sum(1, 2);
    assert(a == 4);
    return 0;
}