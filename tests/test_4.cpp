int main() {
  int x, y;
  int *ptr;
  int *ptr1;

  ptr = &x;
  x = 10;
  y = *ptr;
  assert(y == 10);

  y++;
  x += 10;
  ptr1 = ptr;
  y = *ptr1;
  output(y);

  return 0;
}