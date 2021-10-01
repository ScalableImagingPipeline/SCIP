from pathlib import Path
from datetime import datetime
import uuid
from jinja2 import Environment, FileSystemLoader, select_autoescape


def main():

    output = Path("/vsc-mounts/gent-user/420/vsc42015/vsc_data_vo/results/scip_benchmark")
    output = output / Path("benchmark_%s" % datetime.now().strftime("%Y%m%d%H%M%S"))
    output.mkdir()
    (output / "results").mkdir()

    iterations = 5
    total_mem = 120

    args_fmt = '"--timing %s -j%d -m%d -s%d %s"'

    commands = []
    np = []
    for partition_size in [100, 200, 400, 800]:
        for n_workers in [1, 2, 4, 8, 16, 26]:
            for _ in range(iterations):
                ident = uuid.uuid4()

                timing = str(output / ("%s.json" % ident))
                o = str(output / "results" / str(ident))

                commands.append(
                    args_fmt % (timing, n_workers, total_mem // n_workers, partition_size, o)
                )
                
                # increment n_workers with 2 to accomodate for the client and scheduler process 
                np.append(n_workers+2)

    jinja_env = Environment(
        loader=FileSystemLoader("src/misc"),
        autoescape=select_autoescape()
    )
    jinja_template = jinja_env.get_template("qsub_template.pbs")
    with open(str(output / "qsub.pbs"), "w") as fh:
        fh.write(jinja_template.render(
            number_of_configs=len(commands),
            np_args=" ".join([str(c) for c in np]), 
            args=" ".join(commands)
        ))


if __name__ == "__main__":
    main()
