int main(){
    int i=0;
    int j=0;
    while(i<10){
        if(i>=4){
            i++;
            continue;
        }
        i++;
        j++;
    }
    output(j);  //should print 4
    return 0;
}