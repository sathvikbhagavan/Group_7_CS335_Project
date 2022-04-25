int main(){
    int i=0;
    while(i<10){
        if(i==4){
            break;
        }
        i++;
    }
    output(i);  //should print 4
    return 0;
}