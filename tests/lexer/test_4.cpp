int main() {
    int n = 3;
    bool flag = true;

    for(int i=0; i<1; i++) {
        
        if (i % n == 0) {
            goto l;
        }
        else if(i % n == 1)
        {
            n++;
            continue;
        }
        else {
            break;
        }
    }
l:
    output("Goto");

    return 0;
    
}