int main() {
    int arr[10];
    int i, j, k, sum=0;
    int h;
    for(i=0; i<10; i++) {
        arr[i] = i;
    }

    for(j=1; j<=2; j++) {
        for(k=0; k<10; k++) {
            h = arr[k];
            h = h*h;
            arr[k] = h;
        }
        for(k=0; k<10; k++) {
            h = arr[k];
            sum += h;
        }
    }
    output(sum); // 15618
    return 0;
}