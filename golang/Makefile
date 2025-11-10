# Makefile for VLP to ScreenSteps Converter (Go)

BINARY_NAME=vlp2ss
GO=go
GOFLAGS=-ldflags="-s -w"

.PHONY: all build clean test run install deps help

all: build

## build: Build the binary
build: deps
	@echo "Building $(BINARY_NAME)..."
	$(GO) build $(GOFLAGS) -o $(BINARY_NAME) main.go
	@echo "Build complete: $(BINARY_NAME)"

## deps: Download dependencies
deps:
	@echo "Downloading dependencies..."
	$(GO) mod download
	$(GO) mod tidy

## clean: Remove build artifacts
clean:
	@echo "Cleaning..."
	rm -f $(BINARY_NAME)
	rm -f $(BINARY_NAME)-*
	rm -rf temp/
	rm -rf logs/
	@echo "Clean complete"

## test: Run tests
test:
	@echo "Running tests..."
	$(GO) test -v ./...

## run: Build and run with example
run: build
	./$(BINARY_NAME) --examples

## install: Install the binary to $GOPATH/bin
install: build
	@echo "Installing to /usr/local/bin..."
	cp $(BINARY_NAME) /usr/local/bin/

## cross: Build for multiple platforms
cross: deps
	@echo "Building for multiple platforms..."
	GOOS=linux GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BINARY_NAME)-linux-amd64 main.go
	GOOS=linux GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BINARY_NAME)-linux-arm64 main.go
	GOOS=darwin GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BINARY_NAME)-darwin-amd64 main.go
	GOOS=darwin GOARCH=arm64 $(GO) build $(GOFLAGS) -o $(BINARY_NAME)-darwin-arm64 main.go
	GOOS=windows GOARCH=amd64 $(GO) build $(GOFLAGS) -o $(BINARY_NAME)-windows-amd64.exe main.go
	@echo "Cross-compilation complete"

## help: Show this help message
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@sed -n 's/^##//p' Makefile | column -t -s ':' | sed -e 's/^/ /'

