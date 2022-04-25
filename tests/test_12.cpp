int main(){
    int i;
    for(i=0;i<10;i++){
        if(i==5){
            break;
        }
    }
    output(i);  //should print 5
    return 0;
}