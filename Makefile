ORG := security
PROJECT := deadshot
TAG := $(REPOSITORY)/$(ORG)/$(PROJECT):latest
TEST_IMAGE_NAME := $(ORG)/$(PROJECT)-test
TEST_ARGS:= --volume "$(CURDIR)/build":"/build" --env-file ./configuration/environment/test.env --name deadshot-test $(TEST_IMAGE_NAME)


DOCKER_RUN:= docker run

build:
	docker build . --tag $(PROJECT)
	docker build -f Dockerfile.redis -t $(PROJECT)-redis .

build-test:
	echo $(TEST_IMAGE_NAME)
	docker build --file Dockerfile.test . --tag $(TEST_IMAGE_NAME)

test: build-test clean-test
	$(DOCKER_RUN) $(TEST_ARGS)

serve:
	docker-compose up --build deadshot

clean:
	rm -rf build

clean-test:
	-@docker rm deadshot-test
