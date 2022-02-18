int main(void) {  
    
    char str[20];
    char arr[20]="I love compilers!!!";
    int length;
    strrev(arr);
    strcpy(arr, str);
    length = strlen(arr);
    
    if(strcmp(str, arr)==0){
        output("String Matched");
    }
    else{
        output("Not identical\n");
    }
}    