from Algorithm import Algorithm
from Operation import Operation_Type
from Resource import Resource
from ResourceVersion import ResourceVersion
from Schedule import Schedule
from Transaction import Transaction

class MVTimestampProtocol(Algorithm):
  def __init__(self, schedule: Schedule, outputfilename: str):
    super().__init__(schedule, outputfilename)
    self.name = "Multiversion Timestamp Ordering Protocol"
  
  def execute(self):
    super().execute()
    # Get the max timestamp from transactions
    max_timestamp = 0
    for i in self.transactions:
      if i.ts > max_timestamp:
        max_timestamp = i.ts

    # Execute until the schedule is complete
    while len(self.schedule.operations) > 0:
      operation = self.schedule.operations.pop(0)
      # Only execute multiversion timestamp ordering protocol for operations with a transaction
      if (operation.transaction_id != ""):
        transaction: Transaction = self.get_transaction(operation.transaction_id) # type: ignore
        # Get the most relevant version of the resource for the transaction (<= TS of transaction)
        if operation.resource_name != "":
          res: Resource = self.get_resource(operation.resource_name) # type: ignore
          version_accepted: ResourceVersion = ResourceVersion(0,0,0)
          res.versions.reverse()
          for version in res.versions:
            if version.version <= transaction.ts:
              version_accepted = version
              break
          res.versions.reverse()
        # Handle if read operation
          if operation.op_type == Operation_Type.READ:
            if version_accepted.r_ts < transaction.id:
              version_accepted.r_ts = transaction.id
            super().write(f"-- Transaction {transaction.id} with timestamp {transaction.ts} read version {version_accepted.version} from resource {res.name}")
          # Handle if write operation
          if operation.op_type == Operation_Type.WRITE:
            if transaction.ts < version_accepted.r_ts:
              super().write(f"-- Transaction {transaction.id} with timestamp {transaction.ts} < version {version_accepted.version} of {res.name} read timestamp {version_accepted.r_ts}, rolling back transaction")
              max_timestamp += 1
              # Add last rolled back operation
              transaction.operations_done.append([operation.op_type.name, operation.resource_name])
              self.rollback(transaction, max_timestamp, execute_first=True)
              continue
            elif transaction.ts == version_accepted.w_ts:
              super().write(f"-- Transaction {transaction.id} with timestamp {transaction.ts} = version {version_accepted.version} of {res.name} write timestamp {version_accepted.w_ts}, overwriting value")
            else:
              res.add_version(transaction.ts, transaction.ts)
              super().write(f"-- Transaction {transaction.id} with timestamp {transaction.ts} is writing a new version of {res.name}")
        ret = transaction.do_operation(operation, self.resources[(ord(operation.resource_name)-65)] if  operation.resource_name != "" else "") # type: ignore
        super().write(ret)


inputfile = input("Input file: ")
outputfile = input("Output file: ")
schedule = Schedule(inputfile)
mvprotocol = MVTimestampProtocol(schedule, outputfile)
mvprotocol.execute()
mvprotocol.write(str(mvprotocol))