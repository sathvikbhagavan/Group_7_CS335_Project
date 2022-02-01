int main(void) {  
    
    char str[20];
    char arr[20]="I love compilers!!!";
    strrev(arr);

    int length = strlen(arr);
    strcpy(arr, str);

    if(strcmp(str, arr)==0){
        output("String Matched");
    }
    else{
        output("Not identical\n");
    }
}    