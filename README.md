# Communicating with the HOList proof assistant

HOList is a theorem proving environment based on the HOL Light interactive theorem 
prover.  It turns HOL Light into a machine learning gym environment.  HOList, 
when wrapped in a Docker container, acts as a server which can be interacted 
with via the gRPC standard.  One problem is that those who are familiar with machine
learning may not be familiar with interactive theorem proving and vice versa.  Here,
I will show how to interact with the HOList server, and describe the interface.

## The HOList system (a disambiguation)

### HOList project and website

The name "HOList" has a few meanings all tied to a recent research of Google 
Research.  Most broadly, it is anything that can be found on the 
[HOList website](https://sites.google.com/view/holist/home), including three
papers, a benchmark, two github repositories, and their corresponding Docker images.

### HOList proof assistant server

However, there is also a narrow interpretation of "HOList", and that is what I will
use here.  Narrowly, "HOList" is a fork of the HOL Light interactive theorem prover
which turns it into a machine-learning-focused server.  Before, I unpack that, from
now on, "HOList" will mean the code in 
[github.com/brain-research/hol-light](https://github.com/brain-research/hol-light) and
the Docker image at [gcr.io/deepmath/hol-light](https://gcr.io/deepmath/hol-light).  To
add more confustion, this code and image are labeled HOL Light, not HOList.  The idea is that the
HOList proof assistent is just a fork of the HOL Light interactive theorem prover.  As
with other interactive theorem provers, HOL Light is designed to write proofs in a form
similar to computer code which can be checked by a computer.  Specifically HOL Light is
implemented as a domain specific language onto of OCaml.  It can be used interactively
by a human through the OCaml command line interpreter.  In HOL Light, a user tries to
prove a theorem by first wrapping that thereom into what is called a *goal*.  One can 
then apply *tactics* to this goal which transform the goal into a new goal 
or a new list of goals.  If that returned list is empty, then that goal is now 
solved. The goal (pun not intended) is to keep applying tactics on your goals 
until they are all solved.  Then you have a proof of your theorem.  

What Google's modifications to HOL Light do is that they allow HOL Light to not interact
with a human but with a machine.  This turns HOL Light into a *theorem proving environment*
similar to Open AI's gym environments.  However, because interactive theorem proving has
particular needs, HOList has it's own API which I will describe in just a bit.

### DeepHOL neural proving agent

The other component is the DeepHOL neural proving agent which interacts with 
the HOList server.  The code is at [github.com/tensorflow/deepmath/tree/master/deepmath/deephol](https://github.com/tensorflow/deepmath/tree/master/deepmath/deephol)
and the docker image is here [gcr.io/deepmath/deephol](https://gcr.io/deepmath/deephol). This
is code to train and run Google's specific neural network based theorem proving agent.

### The Docker and gRPC interface

To make things convienient, Google put both HOList and DeepHOL in docker containers.  This lets 
each of the two components run as a black box.  (A Docker container is basically a light 
weight virtual environment.)  The HOList docker container acts as a server and the DeepHOL docker
container acts as a client.  The client makes queries to the server which responds.

```
+----------------+           query            +---------------+
|                | ------------------------>  |               |
| DeepHOL client |      (gRPC standard)       | HOList server | 
|                | <------------------------  |               |
+----------------+         response           +---------------+
```

For example, the DeepHOL client may say "try to apply the tactic `SIMP_TAC` to the goal `x = x`".  The 
server will then respond with an empty list of goals showing that this tactic solved the goal.

The standard by which the client and server communicate is via gRPC which is built on top of 
protoBuf.  The nice thing about this standard is that it lets you easily define common
data structures in a programming language independent way and similarly define an API
for communication between a server and a client.

### proof_assistant.proto

The actual shared specification is stored in a `.proto` file https://github.com/tensorflow/deepmath/blob/master/deepmath/proof_assistant/proof_assistant.proto
(which is also included in the HOList repository).  The most important part of the spec is here:
```
service ProofAssistantService {
  // Apply a tactic to a goal, potentially generating new subgoals.
  rpc ApplyTactic(ApplyTacticRequest) returns (ApplyTacticResponse) {}

  // Verify that a sequence of tactics proves a goal using the proof assistant.
  rpc VerifyProof(VerifyProofRequest) returns (VerifyProofResponse) {}

  // Register a new theorem with the proof assistant and verify/generate
  // its fingerprint. The theorem will be assumed as one that can be used
  // as a valid premise for later proofs.
  rpc RegisterTheorem(RegisterTheoremRequest)
      returns (RegisterTheoremResponse) {}
}
```
It describes the three types of requests one can make of the HOList server.  For the first type of request,
here is the structure of the request and repsonse objects:
```
message ApplyTacticRequest {
  optional Theorem goal = 1;
  optional string tactic = 2;
  optional int64 timeout_ms = 3 [default = 5000];
}

message ApplyTacticResponse {
  oneof result {
    GoalList goals = 1;
    string error = 2;
  }
}
```

## Example communicating with HOList

The spec alone isn't enough to understand what is going on, so we will implement a light weight client which talks to HOList.

### Starting the HOList docker container.

Make sure you have docker running on your machine.  (If not, there are a number of great resources on how to start using docker.)  Then
run the following:
```bash
$ docker run -d -p 2000:2000 --name=holist gcr.io/deepmath/hol-light
```
This is the same [as on the HOList website](https://sites.google.com/view/holist/home#h.p_a1_MzgEdz1qI) except
that instead of using a docker network, we just expose port 2000.  This means we can communicate with HOList via
`localhost:2000`.

Later, when you want to stop the server, just run
```bash
$ docker stop holist && docker rm holist
```

### Running the client

Clone this repository.  Follow [these very simple instructions](https://grpc.io/docs/tutorials/basic/python/) to get the `grpcio` and 
`grpcio_tools` dependencies (and to learn a bit more about gRPC). (Note, this repository includes the automatically created files 
`proof_assistant_pb2.py` and `proof_assistant_pb2_grpc.py`
so you don't have to build those.)  **(TODO: Improve these setup instructions.)**

After that is all setup, you can run the client via:
```bash
$ python3 example_client.py
```

If successful, it should display
```
Request:
 goal {
  conclusion: "(a (c (fun (fun A (bool)) (bool)) !) (l (v A x) (a (a (c (fun A (fun A (bool))) =) (v A x)) (v A x))))"
  tag: THEOREM
  name: "EQ_REFL"
  training_split: TESTING
}
tactic: "SIMP_TAC [ ]"

Response:
 goals {
}
```
This is showing both the request sent (to apply the `SIMP_TAC` to the goal "for all x, x = x"), and the response (no more goals, i.e. it is solved).