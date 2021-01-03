from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_sns as sns
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_stepfunctions as step


class MicroserviceExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        test_queue = sqs.Queue(self, 'test-queue',
                               queue_name='test1')

        test_topic = sns.Topic(self, 'test-topic')

        sns.Subscription(self, 'test-subscription',
                         topic=test_topic,
                         endpoint=test_queue.queue_arn,
                         protocol=sns.SubscriptionProtocol.SQS)

        kinesis.Stream(self, 'test-stream',
                       stream_name='donut-sales',
                       shard_count=2)

        create_order = step.Pass(self, 'create-order',
                                 result=step.Result.from_object({
                                     "Order": {
                                         "Customer": "Alice",
                                         "Product": "Coffee",
                                         "Billing": {"Price": 10.0, "Quantity": 4.0}
                                     }}))
        calculate_amount = step.Pass(self, 'calculate-amount',
                                     result=step.Result.from_number(40.0),
                                     result_path='$.Order.Billing.Amount',
                                     output_path='$.Order.Billing')
        order_definition = create_order.next(calculate_amount)
        step.StateMachine(self, 'test-state-machine',
                          state_machine_name='order-machine',
                          definition=order_definition)

        make_tea = step.Choice(self, 'make-tea',
                               comment='Input should look like {"tea":"green"}')
        green = step.Pass(self, 'green',
                          result=step.Result.from_string('Green tea'))
        make_tea.when(step.Condition.string_equals('$.tea', 'green'), green)
        black = step.Pass(self, 'black',
                          result=step.Result.from_string('Black tea'))
        make_tea.when(step.Condition.string_equals('$.tea', 'black'), black)
        orange = step.Pass(self, 'orange',
                          result=step.Result.from_string('Black tea'))
        make_tea.when(step.Condition.string_equals('$.tea', 'orange'), orange)
        error = step.Pass(self, 'error',
                          result=step.Result.from_string('Bad input'))
        make_tea.otherwise(error)
        step.StateMachine(self, 'test-state-machine-2',
                          state_machine_name='tea-machine',
                          definition=make_tea)
