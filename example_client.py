import logging

import grpc

import proof_assistant_pb2
import proof_assistant_pb2_grpc

# example goals (see https://github.com/tensorflow/deepmath/blob/master/deepmath/deephol/data/mini_theorem_database.textpb)

# equality is reflexive
eq_refl = proof_assistant_pb2.Theorem(
    name="EQ_REFL",
    conclusion="(a (c (fun (fun A (bool)) (bool)) !) (l (v A x) (a (a (c (fun A (fun A (bool))) =) (v A x)) (v A x))))",
    training_split=proof_assistant_pb2.Theorem.Split.TESTING,
    tag=proof_assistant_pb2.Theorem.Tag.THEOREM,
)

# equality is symmetric
eq_sym = proof_assistant_pb2.Theorem(
    name="EQ_SYM",
    conclusion="(a (c (fun (fun A (bool)) (bool)) !) (l (v A x) (a (c (fun (fun A (bool)) (bool)) !) (l (v A y) (a (a (c (fun (bool) (fun (bool) (bool))) ==>) (a (a (c (fun A (fun A (bool))) =) (v A x)) (v A y))) (a (a (c (fun A (fun A (bool))) =) (v A y)) (v A x)))))))",
    training_split=proof_assistant_pb2.Theorem.Split.TESTING,
    tag=proof_assistant_pb2.Theorem.Tag.THEOREM,
)

# this goal is intentially false: for all x and y, x = y
a_equals_b = proof_assistant_pb2.Theorem(
    name="A_EQUALS_B",
    conclusion="(a (c (fun (fun A (bool)) (bool)) !) (l (v A x) (a (c (fun (fun A (bool)) (bool)) !) (l (v A y) (a (a (c (fun A (fun A (bool))) =) (v A x)) (v A y))))))",
    training_split=proof_assistant_pb2.Theorem.Split.TESTING,
    tag=proof_assistant_pb2.Theorem.Tag.THEOREM,
)


# example tactics  (see https://github.com/tensorflow/deepmath/blob/master/deepmath/deephol/data/hollight_tactics.textpb for more)
asm_meson_tac = "ASM_MESON_TAC [ ]"
simp_tac = "SIMP_TAC [ ]"
refl_tac = "REFL_TAC"
ants_tac = "ANTS_TAC"

def run():
    with grpc.insecure_channel('localhost:2000') as channel:
        stub = proof_assistant_pb2_grpc.ProofAssistantServiceStub(channel)

        request = proof_assistant_pb2.ApplyTacticRequest(goal=eq_refl, tactic=simp_tac)
        print("Request:\n", request)

        response = stub.ApplyTactic(request)
        print("Response:\n", response)


if __name__ == '__main__':
    logging.basicConfig()
    run()