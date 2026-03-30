PREFIX     ?= $(HOME)/.letcook
BIN_DIR    ?= $(HOME)/.local/bin
SHELL      := bash

.PHONY: install uninstall link help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install letcook to ~/.letcook and symlink to ~/.local/bin
	@echo "Installing to $(PREFIX)..."
	@mkdir -p $(PREFIX)
	@cp -r bin templates integrations skill.md $(PREFIX)/
	@chmod +x $(PREFIX)/bin/letcook
	@mkdir -p $(BIN_DIR)
	@ln -sf $(PREFIX)/bin/letcook $(BIN_DIR)/letcook
	@echo ""
	@echo "Installed. Make sure $(BIN_DIR) is in your PATH:"
	@echo ""
	@echo '  export PATH="$$HOME/.local/bin:$$PATH"'
	@echo ""
	@echo "Then run:"
	@echo ""
	@echo "  letcook init ./my-task"
	@echo ""

uninstall: ## Remove letcook from ~/.letcook and ~/.local/bin
	@echo "Removing $(PREFIX)..."
	@rm -rf $(PREFIX)
	@rm -f $(BIN_DIR)/letcook
	@echo "Uninstalled."

link: ## Symlink from repo (for development)
	@mkdir -p $(BIN_DIR)
	@ln -sf $(CURDIR)/bin/letcook $(BIN_DIR)/letcook
	@echo "Linked $(BIN_DIR)/letcook → $(CURDIR)/bin/letcook"
