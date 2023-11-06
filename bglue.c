/* Basic glue lib to hold the transpiled output together.
 * Eventually this will just have ONLY the main function, but for now it
 * also has puts() because I wanted to test writing 'hello world' without
 * having to implement more of the transpiler
 */

#include <stdio.h>

#define bword_t void*

void B_puts(bword_t str) {
	printf((char*)str);
}

bword_t B_main(bword_t argc, bword_t argv);

int main(int argc, char **argv) {
	return B_main((bword_t)argc, (bword_t)argv);
}
