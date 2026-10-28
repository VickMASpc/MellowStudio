import json
from PIL import Image
from mellowstudio.samples import mellow_document
from mellowstudio.model import project_save
from mellowstudio.cli import main, project_info


def test_cli_batch_sheet_and_frames(tmp_path, capsys):
    d=mellow_document()
    d.duplicate_frame(linked=True)
    p=tmp_path/'project.mellowzip'
    project_save(d,p)
    assert main(['validate',str(p)])==0
    assert 'VALID' in capsys.readouterr().out
    assert main(['info',str(p)])==0
    info=json.loads(capsys.readouterr().out)
    assert info['linked_exposure_groups'][d.layer.name]==[[1,2]]
    sheet=tmp_path/'sheet.png'
    main(['export',str(p),'--format','sheet','--out',str(sheet)])
    assert Image.open(sheet).size==(82,55)
    assert json.loads((tmp_path/'sheet.json').read_text())['durations_ms']==[100,100]
    folder=tmp_path/'frames'
    main(['export',str(p),'--format','frames','--out',str(folder)])
    assert Image.open(folder/'frame_0001.png').size==(41,55)
    assert (folder/'frames.json').exists()
