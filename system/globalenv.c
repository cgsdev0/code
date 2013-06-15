#define _GNU_SOURCE
#include <sys/types.h>
#include <stdio.h>
#include <keyutils.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <util.h>

char *arg0;

key_serial_t def_keyring = KEY_SPEC_USER_KEYRING;

static int usage() {
	printf("Usage: %s <program> [<args>...]\n", arg0);
	printf("       %s -s <env>...\n", arg0);
	printf("       %s -x\n", arg0);
	return 2;
}

struct Env {
	key_serial_t id;
	char *name;
	struct Env *next;
};

struct Env * Env_enum(void) {
	key_serial_t *ringp, *keyp;
	size_t ringz;
	struct Env *env = NULL, *lastenv = NULL;

	ringz = keyctl_read_alloc(def_keyring, (void**)&ringp);

	for (keyp = ringp;
	     ringz > 0;
	     ringz -= sizeof(key_serial_t), ++keyp)
	{
		_cleanup_free_ char *rdesc = NULL;
		char *desc;

		keyctl_describe_alloc(*keyp, &rdesc);
		if (strncmp(rdesc, "user;", 5))
			continue;

		desc = strrchr(rdesc, ';') + 1;
		if (strncmp(desc, "env:", 4))
			continue;

		lastenv = env;
		env = malloc(sizeof(struct Env));
		env->id = *keyp;
		env->name = strdup(desc + 4);
		env->next = lastenv;
	}

	free(ringp);

	return env;
}

#define Env_each(var, lvar) for (var = lvar; var; var = var->next)

void Env_free(struct Env *ptr) {
	struct Env *next;

	while (ptr) {
		next = ptr->next;
		free(ptr->name);
		free(ptr);
		ptr = next;
	}
}

void update_key(char *name) {
	char *value;
	_cleanup_free_ char *desc;
	key_serial_t id;

	if (name[0] == '+') {
		name++;
		if (strchr(name, '=')) {
			fprintf(stderr, "%s: Invalid variable name '%s'\n",
				arg0, name);
			return;
		}
		value = getenv(name);
	} else {
		value = strchr(name, '=');
		if (value)
			*value++ = '\0';
	}
	
	asprintf(&desc, "env:%s", name);

	if (value && *value) {
		id = add_key("user", desc, (void *)value,
		             strlen(value), def_keyring);
	} else {
		id = keyctl_search(def_keyring, "user", desc, 0);

		if (id)
			keyctl_unlink(id, def_keyring);
	}
}

void remove_all_keys() {
	struct Env *envlistp, *envp;

	envlistp = Env_enum();

	Env_each(envp, envlistp) {
		keyctl_unlink(envp->id, def_keyring);
	}

	Env_free(envlistp);
}

int run_with_env(int argc, char *argv[]) {
	struct Env *envlistp, *envp;
	int r;

	envlistp = Env_enum();

	Env_each(envp, envlistp) {
		_cleanup_free_ char *value = NULL;

		keyctl_read_alloc(envp->id, (void**)&value);
		if (argc)
			setenv(envp->name, value, true);
		else
			printf("%s=%s\n", envp->name, value);
	}

	Env_free(envlistp);

	if (argc) {
		r = execvp(argv[0], argv);
		if (r < 0) {
			fprintf(stderr, "%s: Could not run '%s': %m\n",
				arg0, argv[0]);
			return 1;
		}
	}

	return 0;
}

int main(int argc, char *argv[]) {
	int opt, mode = 0;

	arg0 = argv[0];

	while ((opt = getopt(argc, argv, "+sx")) != -1) {
		switch (opt) {
		case 's':
		case 'x':
			mode = opt;
			break;
		default:
			return usage();
		}
	}

	argc -= optind;
	argv += optind;

	if (mode == 's') {
		while (*argv)
			update_key(*argv++);
		return 0;
	} else if (mode == 'x') {
		remove_all_keys();
		return 0;
	} else {
		return run_with_env(argc, argv);
	}
}
